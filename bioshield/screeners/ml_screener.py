import os
import joblib
import numpy as np
from bioshield.screeners.base import BaseScreener, ScreenResult
from bioshield.ml.features import extract_features, feature_dict_to_vector, FEATURE_NAMES

class MLScreener(BaseScreener):
    """
    Layer 2: ML Ensemble + Meta-Learner.
    Random Forest + XGBoost base models, with a Logistic Regression
    meta-learner that learns how much to trust each model's output.
    """
    
    def __init__(self, rf_path: str, xgb_path: str, threshold: float = 0.70, meta_path: str = None):
        self.rf_path = rf_path
        self.xgb_path = xgb_path
        self.meta_path = meta_path
        self.threshold = threshold
        self.rf_model = None
        self.xgb_model = None
        self.meta_model = None
        self._load_models()
        
    def _load_models(self):
        if os.path.exists(self.rf_path):
            self.rf_model = joblib.load(self.rf_path)
            
        if os.path.exists(self.xgb_path):
            self.xgb_model = joblib.load(self.xgb_path)

        if self.meta_path and os.path.exists(self.meta_path):
            self.meta_model = joblib.load(self.meta_path)

    def screen(self, sequence: str, sequence_id: str = "unknown") -> ScreenResult:
        if not self.rf_model and not self.xgb_model:
            return ScreenResult(
                layer_name=self.name, flagged=False, confidence=0.0,
                explanation="No ML models loaded.",
                details={"error": "models_not_found"}
            )
            
        features_dict = extract_features(sequence)
        features_vec = feature_dict_to_vector(features_dict).reshape(1, -1)
        
        probs = []
        importances = {}
        
        rf_prob = None
        xgb_prob = None
        
        if self.rf_model:
            rf_prob = float(self.rf_model.predict_proba(features_vec)[0, 1])
            probs.append(rf_prob)
            rf_importances = self.rf_model.feature_importances_
            for i, name in enumerate(FEATURE_NAMES):
                importances[name] = importances.get(name, 0) + float(rf_importances[i])
                
        if self.xgb_model:
            xgb_prob = float(self.xgb_model.predict_proba(features_vec)[0, 1])
            probs.append(xgb_prob)
            xgb_importances = self.xgb_model.feature_importances_
            for i, name in enumerate(FEATURE_NAMES):
                importances[name] = importances.get(name, 0) + float(xgb_importances[i])
        
        # Use meta-learner if available, otherwise average
        if self.meta_model and rf_prob is not None and xgb_prob is not None:
            meta_input = np.array([[rf_prob, xgb_prob]])
            avg_prob = float(self.meta_model.predict_proba(meta_input)[0, 1])
            meta_used = True
        else:
            avg_prob = sum(probs) / len(probs)
            meta_used = False
            
        is_flagged = avg_prob >= self.threshold
        
        if is_flagged:
            top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:3]
            top_feature_names = [f[0] for f in top_features]
            mode = "Meta-Learner" if meta_used else "Ensemble avg"
            explanation = f"ML ensemble detected threat pattern (prob={avg_prob:.2f}, {mode}). Driven by: {', '.join(top_feature_names)}."
        else:
            explanation = f"Sequence classified as safe by ML ensemble (prob={avg_prob:.2f})."
            
        return ScreenResult(
            layer_name=self.name, flagged=is_flagged,
            confidence=avg_prob if is_flagged else (1.0 - avg_prob),
            explanation=explanation,
            details={
                "probability": avg_prob,
                "rf_prob": rf_prob,
                "xgb_prob": xgb_prob,
                "meta_learner_used": meta_used,
                "features": features_dict,
                "feature_importances": importances
            }
        )
