import os
import joblib
import numpy as np
from bioshield.screeners.base import BaseScreener, ScreenResult
from bioshield.ml.features import extract_features, feature_dict_to_vector, FEATURE_NAMES

class MLScreener(BaseScreener):
    """
    Screens sequences using a trained ensemble of Random Forest and XGBoost.
    Catches complex, non-linear threat patterns and provides interpretable feature importances.
    """
    
    def __init__(self, rf_path: str, xgb_path: str, threshold: float = 0.70):
        self.rf_path = rf_path
        self.xgb_path = xgb_path
        self.threshold = threshold
        self.rf_model = None
        self.xgb_model = None
        self._load_models()
        
    def _load_models(self):
        if os.path.exists(self.rf_path):
            self.rf_model = joblib.load(self.rf_path)
        else:
            print(f"Warning: RF model not found at {self.rf_path}.")
            
        if os.path.exists(self.xgb_path):
            self.xgb_model = joblib.load(self.xgb_path)
        else:
            print(f"Warning: XGB model not found at {self.xgb_path}.")

    def screen(self, sequence: str, sequence_id: str = "unknown") -> ScreenResult:
        if not self.rf_model and not self.xgb_model:
            return ScreenResult(
                layer_name=self.name,
                flagged=False,
                confidence=0.0,
                explanation="No ML models loaded.",
                details={"error": "models_not_found"}
            )
            
        # Extract features
        features_dict = extract_features(sequence)
        features_vec = feature_dict_to_vector(features_dict).reshape(1, -1)
        
        probs = []
        importances = {}
        
        if self.rf_model:
            prob = float(self.rf_model.predict_proba(features_vec)[0, 1]) # Probability of class 1 (Threat)
            probs.append(prob)
            rf_importances = self.rf_model.feature_importances_
            for i, name in enumerate(FEATURE_NAMES):
                importances[name] = importances.get(name, 0) + float(rf_importances[i])
                
        if self.xgb_model:
            prob = float(self.xgb_model.predict_proba(features_vec)[0, 1])
            probs.append(prob)
            xgb_importances = self.xgb_model.feature_importances_
            for i, name in enumerate(FEATURE_NAMES):
                importances[name] = importances.get(name, 0) + float(xgb_importances[i])
                
        # Average probability
        avg_prob = sum(probs) / len(probs)
        is_flagged = avg_prob >= self.threshold
        
        # Determine explanation
        if is_flagged:
            # Sort features by importance
            top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:3]
            top_feature_names = [f[0] for f in top_features]
            explanation = f"ML ensemble detected threat pattern (prob={avg_prob:.2f}). Driven by: {', '.join(top_feature_names)}."
        else:
            explanation = f"Sequence classified as safe by ML ensemble (prob={avg_prob:.2f})."
            
        return ScreenResult(
            layer_name=self.name,
            flagged=is_flagged,
            confidence=avg_prob if is_flagged else (1.0 - avg_prob),
            explanation=explanation,
            details={
                "probability": avg_prob,
                "features": features_dict,
                "feature_importances": importances
            }
        )
