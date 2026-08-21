import datetime
import json
import os
import time
from typing import Any, Dict, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.utils import resample

from app.config import MODELS_DIR, REPORTS_DIR, settings
from app.ml.evaluator import evaluate_model, plot_and_save_confusion_matrix
from app.ml.preprocessor import TextCleaner, build_combined_text_series


def load_dataset(csv_path: Optional[str] = None) -> pd.DataFrame:
    """Loads and standardizes the recruitment fraud dataset."""
    path = csv_path or settings.DATASET_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found at path: {path}")
        
    df = pd.read_csv(path)
    
    # Standardize column names if needed
    col_mapping = {
        "job_title": "title",
        "job_description": "description",
        "education_level": "required_education",
        "required_experience_years": "required_experience",
        "is_fake": "fraudulent",
    }
    df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns}, inplace=True)
    
    if "fraudulent" not in df.columns:
        raise ValueError("Dataset missing 'fraudulent' label column.")
        
    # Drop rows where fraudulent is missing or invalid
    df = df.dropna(subset=["fraudulent"])
    df["fraudulent"] = df["fraudulent"].astype(int)
    
    return df


def resample_to_ratio(
    X_train: pd.Series,
    y_train: pd.Series,
    target_genuine_ratio: float = 0.70,
    target_fraud_ratio: float = 0.30,
    random_state: int = 42
) -> Tuple[pd.Series, pd.Series]:
    """
    Resamples the training split to achieve the target 70% genuine / 30% fraud ratio.
    Stratified split is performed BEFORE this call, guaranteeing zero test set leakage.
    """
    train_df = pd.DataFrame({"text": X_train, "fraudulent": y_train})
    genuine_df = train_df[train_df["fraudulent"] == 0]
    fraud_df = train_df[train_df["fraudulent"] == 1]
    
    n_genuine = len(genuine_df)
    # Calculate target fraud count to achieve 70/30 ratio:
    # n_fraud / (n_genuine + n_fraud) = 0.30 => n_fraud = n_genuine * (0.30 / 0.70)
    target_n_fraud = int(n_genuine * (target_fraud_ratio / target_genuine_ratio))
    
    print(f"[*] Resampling training split: Original Fraud: {len(fraud_df)}, Target Fraud: {target_n_fraud}, Genuine: {n_genuine}")
    
    fraud_upsampled = resample(
        fraud_df,
        replace=True,
        n_samples=target_n_fraud,
        random_state=random_state
    )
    
    balanced_train_df = pd.concat([genuine_df, fraud_upsampled]).sample(frac=1, random_state=random_state)
    return balanced_train_df["text"], balanced_train_df["fraudulent"]


def train_models(
    csv_path: Optional[str] = None,
    save_artifacts: bool = True
) -> Dict[str, Any]:
    """
    Complete ML Pipeline:
    1. Preprocessing & Text Combination
    2. Stratified Train (70%) / Val (15%) / Test (15%) Split
    3. Resampling Training Set to 70% Genuine / 30% Fraudulent
    4. TF-IDF Feature Extraction
    5. Training Logistic Regression & Random Forest
    6. Objective Evaluation on Balanced Val and Untouched Real-World Test Sets
    7. Model Serialization & Comparison Metadata
    """
    start_time = time.perf_counter()
    print("[*] Loading dataset...")
    df = load_dataset(csv_path)
    print(f"[+] Loaded {len(df)} postings ({df['fraudulent'].sum()} fraudulent, {len(df) - df['fraudulent'].sum()} genuine).")
    
    # 1. Feature Preprocessing
    print("[*] Building combined text representation...")
    df["combined_text"] = build_combined_text_series(df)
    
    # Filter empty texts
    valid_mask = df["combined_text"].str.strip() != ""
    df = df[valid_mask].reset_index(drop=True)
    
    X = df["combined_text"]
    y = df["fraudulent"]
    
    # 2. Stratified Train / Val / Test Split (70 / 15 / 15)
    print("[*] Performing Stratified Train (70%) / Val (15%) / Test (15%) Split...")
    X_train_raw, X_temp, y_train_raw, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )
    
    print(f"    - Train raw: {len(X_train_raw)} (Fraud: {y_train_raw.sum()} / {(y_train_raw.mean()*100):.2f}%)")
    print(f"    - Val:       {len(X_val)} (Fraud: {y_val.sum()} / {(y_val.mean()*100):.2f}%)")
    print(f"    - Test (Untouched): {len(X_test)} (Fraud: {y_test.sum()} / {(y_test.mean()*100):.2f}%)")
    
    # 3. Resample Training Set to 70/30 ratio
    X_train_resampled, y_train_resampled = resample_to_ratio(
        X_train_raw, y_train_raw, target_genuine_ratio=0.70, target_fraud_ratio=0.30, random_state=42
    )
    print(f"    - Train resampled: {len(X_train_resampled)} (Fraud: {y_train_resampled.sum()} / {(y_train_resampled.mean()*100):.2f}%)")
    
    # 4. TF-IDF Vectorization
    print("[*] Fitting TF-IDF Vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=15000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=2
    )
    X_train_vec = vectorizer.fit_transform(X_train_resampled)
    X_val_vec = vectorizer.transform(X_val)
    X_test_vec = vectorizer.transform(X_test)
    
    # 5. Train Model 1: Logistic Regression
    print("[*] Training Model 1: TF-IDF + Logistic Regression (balanced weights)...")
    lr_model = LogisticRegression(
        class_weight="balanced",
        C=1.5,
        max_iter=1000,
        random_state=42
    )
    lr_model.fit(X_train_vec, y_train_resampled)
    
    # 6. Train Model 2: Random Forest
    print("[*] Training Model 2: TF-IDF + Random Forest (balanced weights)...")
    rf_model = RandomForestClassifier(
        n_estimators=150,
        max_depth=35,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train_vec, y_train_resampled)
    
    # 7. Comprehensive Evaluation
    print("[*] Evaluating models on validation and untouched test sets...")
    
    # Evaluate Logistic Regression
    lr_val_metrics = evaluate_model(lr_model, X_val_vec, y_val.values, "Logistic Regression", "Validation Set")
    lr_test_metrics = evaluate_model(lr_model, X_test_vec, y_test.values, "Logistic Regression", "Untouched Real-World Test Set")
    
    # Evaluate Random Forest
    rf_val_metrics = evaluate_model(rf_model, X_val_vec, y_val.values, "Random Forest", "Validation Set")
    rf_test_metrics = evaluate_model(rf_model, X_test_vec, y_test.values, "Random Forest", "Untouched Real-World Test Set")
    
    # 8. Objective Model Comparison (Fraud Recall and F1 as Headline)
    print("\n" + "="*80)
    print("OBJECTIVE MODEL COMPARISON ON UNTOUCHED REAL-WORLD TEST SET (~4.8% Fraud)")
    print("="*80)
    print(f"{'Metric':<25} | {'Logistic Regression':<22} | {'Random Forest':<22}")
    print("-"*80)
    print(f"{'Fraud Recall (Headline)':<25} | {lr_test_metrics['fraud_recall']:<22.4f} | {rf_test_metrics['fraud_recall']:<22.4f}")
    print(f"{'Fraud Precision':<25} | {lr_test_metrics['fraud_precision']:<22.4f} | {rf_test_metrics['fraud_precision']:<22.4f}")
    print(f"{'Fraud F1 (Headline)':<25} | {lr_test_metrics['fraud_f1']:<22.4f} | {rf_test_metrics['fraud_f1']:<22.4f}")
    print(f"{'ROC-AUC':<25} | {lr_test_metrics['roc_auc']:<22.4f} | {rf_test_metrics['roc_auc']:<22.4f}")
    print(f"{'PR-AUC':<25} | {lr_test_metrics['pr_auc']:<22.4f} | {rf_test_metrics['pr_auc']:<22.4f}")
    print(f"{'Accuracy':<25} | {lr_test_metrics['accuracy']:<22.4f} | {rf_test_metrics['accuracy']:<22.4f}")
    print("="*80 + "\n")
    
    # Select Champion based on headline metric (Fraud F1 / Recall)
    if lr_test_metrics["fraud_f1"] >= rf_test_metrics["fraud_f1"]:
        champion_name = "Logistic Regression"
        champion_model = lr_model
        champion_test_metrics = lr_test_metrics
    else:
        champion_name = "Random Forest"
        champion_model = rf_model
        champion_test_metrics = rf_test_metrics
        
    print(f"[+] Champion Model Selected: {champion_name} (Fraud F1: {champion_test_metrics['fraud_f1']:.4f}, Recall: {champion_test_metrics['fraud_recall']:.4f})")
    
    # 9. Save Artifacts & Figures
    if save_artifacts:
        print("[*] Persisting models, vectorizer, and metadata...")
        joblib.dump(vectorizer, settings.VECTORIZER_PATH)
        joblib.dump(lr_model, settings.LOGISTIC_REGRESSION_PATH)
        joblib.dump(rf_model, settings.RANDOM_FOREST_PATH)
        joblib.dump(champion_model, settings.CHAMPION_MODEL_PATH)
        
        # Save Confusion Matrices
        lr_cm = np.array([
            [lr_test_metrics["confusion_matrix"]["true_negatives"], lr_test_metrics["confusion_matrix"]["false_positives"]],
            [lr_test_metrics["confusion_matrix"]["false_negatives"], lr_test_metrics["confusion_matrix"]["true_positives"]]
        ])
        rf_cm = np.array([
            [rf_test_metrics["confusion_matrix"]["true_negatives"], rf_test_metrics["confusion_matrix"]["false_positives"]],
            [rf_test_metrics["confusion_matrix"]["false_negatives"], rf_test_metrics["confusion_matrix"]["true_positives"]]
        ])
        
        fig_dir = os.path.join(str(REPORTS_DIR), "figures")
        plot_and_save_confusion_matrix(lr_cm, "Logistic Regression", os.path.join(fig_dir, "cm_logistic_regression.png"), "(Test Set)")
        plot_and_save_confusion_matrix(rf_cm, "Random Forest", os.path.join(fig_dir, "cm_random_forest.png"), "(Test Set)")
        
        # Save Metadata JSON
        metadata = {
            "version": "v1.0.0",
            "training_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "dataset_version": "Kaggle_EMSCAD_17880",
            "total_dataset_rows": len(df),
            "training_distribution": {
                "train_resampled_genuine": int((y_train_resampled == 0).sum()),
                "train_resampled_fraud": int((y_train_resampled == 1).sum()),
                "train_ratio": "70% Genuine / 30% Fraud",
                "test_untouched_genuine": int((y_test == 0).sum()),
                "test_untouched_fraud": int((y_test == 1).sum()),
                "test_fraud_rate": round(float(y_test.mean()), 4)
            },
            "champion_model": champion_name,
            "models": {
                "logistic_regression": {
                    "validation_metrics": lr_val_metrics,
                    "test_metrics": lr_test_metrics
                },
                "random_forest": {
                    "validation_metrics": rf_val_metrics,
                    "test_metrics": rf_test_metrics
                }
            },
            "elapsed_seconds": round(time.perf_counter() - start_time, 2)
        }
        
        with open(settings.MODEL_METADATA_PATH, "w") as f:
            json.dump(metadata, f, indent=2)
            
        print(f"[+] Model artifacts and metadata written to {MODELS_DIR}")
        
    return {
        "champion_name": champion_name,
        "logistic_regression_test": lr_test_metrics,
        "random_forest_test": rf_test_metrics,
        "elapsed_seconds": time.perf_counter() - start_time
    }


if __name__ == "__main__":
    train_models()
