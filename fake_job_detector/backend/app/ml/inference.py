import os
import time
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd

from app.config import settings
from app.ml.preprocessor import TextCleaner, build_combined_text_from_dict


class MLInferenceEngine:
    """Thread-safe, high-performance ML inference runner for fraud classification."""
    
    _instance: Optional["MLInferenceEngine"] = None
    
    def __init__(self):
        self.vectorizer = None
        self.logistic_regression = None
        self.random_forest = None
        self.champion_model = None
        self.feature_names: Optional[np.ndarray] = None
        self.is_loaded: bool = False
        self.load_models()

    @classmethod
    def get_instance(cls) -> "MLInferenceEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_models(self, force_reload: bool = False):
        """Loads models and TF-IDF vectorizer into memory."""
        if self.is_loaded and not force_reload:
            return
            
        print("[*] Loading ML models into memory...")
        if os.path.exists(settings.VECTORIZER_PATH):
            self.vectorizer = joblib.load(settings.VECTORIZER_PATH)
            self.feature_names = np.array(self.vectorizer.get_feature_names_out())
            
        if os.path.exists(settings.LOGISTIC_REGRESSION_PATH):
            self.logistic_regression = joblib.load(settings.LOGISTIC_REGRESSION_PATH)
            
        if os.path.exists(settings.RANDOM_FOREST_PATH):
            self.random_forest = joblib.load(settings.RANDOM_FOREST_PATH)
            
        if os.path.exists(settings.CHAMPION_MODEL_PATH):
            self.champion_model = joblib.load(settings.CHAMPION_MODEL_PATH)
        elif self.logistic_regression:
            self.champion_model = self.logistic_regression

        self.is_loaded = (self.vectorizer is not None and self.champion_model is not None)
        if self.is_loaded:
            print("[+] ML Inference Engine loaded successfully.")
        else:
            print("[!] Warning: ML models not found on disk. Run trainer first.")

    def predict_text(
        self,
        text: str,
        model_type: str = "champion",
        top_k_features: int = 6
    ) -> Dict[str, Any]:
        """
        Runs ML inference on a text string.
        Returns:
            - fraud_probability (0.0 to 1.0)
            - is_fraud (bool)
            - top_features: list of top contributing tokens and weights
            - inference_time_ms
        """
        t0 = time.perf_counter()
        if not self.is_loaded:
            self.load_models()
            
        if not self.is_loaded or self.vectorizer is None:
            return {
                "fraud_probability": 0.1,
                "is_fraud": False,
                "model_used": "fallback",
                "top_features": [],
                "inference_time_ms": 0.0
            }
            
        # Select Model
        if model_type == "logistic_regression" and self.logistic_regression:
            model = self.logistic_regression
        elif model_type == "random_forest" and self.random_forest:
            model = self.random_forest
        else:
            model = self.champion_model or self.logistic_regression
            model_type = "champion"
            
        # Transform text
        vec = self.vectorizer.transform([text])
        
        # Compute probability
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(vec)[0]
            fraud_prob = float(probs[1])
        else:
            pred = model.predict(vec)[0]
            fraud_prob = 0.95 if pred == 1 else 0.05
            
        # Extract Top Contributing Features (from LR or active tokens)
        top_features = []
        if self.feature_names is not None and vec.nnz > 0:
            nz_indices = vec.indices
            nz_values = vec.data
            
            if hasattr(self.logistic_regression, "coef_"):
                lr_coefs = self.logistic_regression.coef_[0]
                feature_scores = []
                for idx, val in zip(nz_indices, nz_values):
                    term = self.feature_names[idx]
                    weight = float(lr_coefs[idx] * val)
                    feature_scores.append({"term": term, "weight": round(weight, 4)})
                    
                # Sort by highest positive weight (pushing toward fraud)
                feature_scores.sort(key=lambda x: x["weight"], reverse=True)
                top_features = feature_scores[:top_k_features]
            else:
                # Fallback to highest TF-IDF values
                top_indices = nz_indices[np.argsort(-nz_values)[:top_k_features]]
                top_features = [{"term": self.feature_names[i], "weight": round(float(vec[0, i]), 4)} for i in top_indices]

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "fraud_probability": round(fraud_prob, 4),
            "is_fraud": bool(fraud_prob >= 0.5),
            "model_used": model_type,
            "top_features": top_features,
            "inference_time_ms": elapsed_ms
        }

    def predict_job(self, job_dict: Dict[str, Any], model_type: str = "champion") -> Dict[str, Any]:
        """Runs ML inference on a full structured job dictionary."""
        combined_text = build_combined_text_from_dict(job_dict)
        return self.predict_text(combined_text, model_type=model_type)
