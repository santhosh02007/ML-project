import json
import os
from typing import Any, Dict, Optional, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def evaluate_model(
    model: Any,
    X_test: Any,
    y_test: np.ndarray,
    model_name: str = "Model",
    dataset_name: str = "Test Set"
) -> Dict[str, Any]:
    """
    Evaluates a binary classification model with emphasis on fraud recall, precision, and F1.
    """
    # Predictions and Probabilities
    y_pred = model.predict(X_test)
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)[:, 1]
    elif hasattr(model, "decision_function"):
        # Calibrated/scaled decision function
        dec = model.decision_function(X_test)
        y_prob = 1 / (1 + np.exp(-dec))
    else:
        y_prob = y_pred.astype(float)

    # Core Metrics
    acc = float(accuracy_score(y_test, y_pred))
    fraud_rec = float(recall_score(y_test, y_pred, pos_label=1, zero_division=0))
    fraud_prec = float(precision_score(y_test, y_pred, pos_label=1, zero_division=0))
    fraud_f1 = float(f1_score(y_test, y_pred, pos_label=1, zero_division=0))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

    try:
        roc_auc = float(roc_auc_score(y_test, y_prob))
    except Exception:
        roc_auc = 0.5

    try:
        pr_auc = float(average_precision_score(y_test, y_prob))
    except Exception:
        pr_auc = 0.0

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    metrics = {
        "model_name": model_name,
        "dataset_name": dataset_name,
        "total_samples": int(len(y_test)),
        "genuine_samples": int((y_test == 0).sum()),
        "fraud_samples": int((y_test == 1).sum()),
        "accuracy": round(acc, 4),
        "fraud_recall": round(fraud_rec, 4),        # Headline Metric
        "fraud_precision": round(fraud_prec, 4),    # Headline Metric
        "fraud_f1": round(fraud_f1, 4),            # Headline Metric
        "macro_f1": round(macro_f1, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "classification_report": report_dict
    }

    return metrics


def plot_and_save_confusion_matrix(
    cm: np.ndarray,
    model_name: str,
    output_path: str,
    title_suffix: str = ""
):
    """Generates and saves a clean confusion matrix heatmap."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.figure(figsize=(6, 5), dpi=150)
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Genuine (0)", "Fraudulent (1)"],
        yticklabels=["Genuine (0)", "Fraudulent (1)"],
        cbar=False
    )
    plt.title(f"Confusion Matrix: {model_name} {title_suffix}", fontsize=12, fontweight="bold")
    plt.xlabel("Predicted Label", fontsize=10)
    plt.ylabel("Ground Truth Label", fontsize=10)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
