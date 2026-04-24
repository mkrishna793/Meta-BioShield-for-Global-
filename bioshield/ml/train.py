import os
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from bioshield.ml.features import extract_features, feature_dict_to_vector
from sklearn.model_selection import cross_val_score

def build_mock_training_data():
    """Generates synthetic training data for the hackathon."""
    # Class 0: Safe (e.g. GFP, common lab genes)
    safe_seqs = [
        "ATGCGTAAAGGCGAAGAGCTGTTCACTGGTGTCGTCCCTATTCTGGTGGAACTGGATGGTGATGTCAACGGTCATAAGTTTTCCGTGCGTGGCGAGGGTGAAGGTGACGCAACTAATGGTAAACTGACGCTGAAGTTCATCTGTACTACTGGTAAACTGCCGGTTCCTTGGCCGACTCTGGTAACGACGCTGACTTATGGTGTTCAGTGCTTTGCTCGTTATCCGGACCATATGAAGCAGCATGACTTCTTCAAGTCCGCCATGCCGGAAGGCTATGTGCAGGAACGCACGATTTCCTTTAAGGATGACGGCACGTACAAAACGCGTGCGGAAGTGAAATTTGAAGGCGATACCCTGGTAAACCGCATTGAGCTGAAAGGCATTGACTTTAAAGAAGACGGCAATATCCTGGGCCATAAGCTGGAATACAATTTTAACAGCCACAATGTTTACATCACCGCCGATAAACAAAAAAATGGCATTAAAGCGAATTTTAAAATTCGCCACAACGTGGAGGATGGCAGCGTGCAGCTGGCTGATCACTACCAGCAAAACACTCCAATCGGTGATGGTCCTGTTCTGCTGCCAGACAATCACTATCTGAGCACGCAAAGCGTTCTGTCTAAAGATCCGAACGAGAAACGCGATCATATGGTTCTGCTGGAGTTCGTAACCGCAGCGGGCATCACGCATGGTATGGATGAACTGTACAAATAA",  # GFP
        "TTAACTCGAGGATCC" * 10, # Generic vector stuff
        "ATGCCTGAATC" * 30      # Random safe sequence
    ]
    
    # Class 1: Threat (e.g. Toxin fragments, virulence factors, and AI-shuffled variants)
    threat_seqs = [
        "ATGCATGCATGC" * 50 + "TATA" * 20, # Anthrax mock (from kmer db)
        "CGCGCGCG" * 50 + "GATC" * 20,     # Variola mock
        "CCCGGGAAATTT" * 40,               # High repeat density threat
        "ATGCGTAAA" * 10 + "TGA" * 5 + "ATGC" * 20 # Broken ORF threat
    ]
    
    X = []
    y = []
    
    for seq in safe_seqs:
        X.append(feature_dict_to_vector(extract_features(seq)))
        y.append(0)
        
    for seq in threat_seqs:
        X.append(feature_dict_to_vector(extract_features(seq)))
        y.append(1)
        
    return np.array(X), np.array(y)

def train_models():
    print("Generating mock training data...")
    X, y = build_mock_training_data()
    
    print(f"Training on {len(X)} samples ({sum(y==1)} threats, {sum(y==0)} safe)...")
    
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    xgb = XGBClassifier(n_estimators=100, max_depth=5, random_state=42, eval_metric='logloss')
    
    rf.fit(X, y)
    xgb.fit(X, y)
    
    # Evaluate
    rf_scores = cross_val_score(rf, X, y, cv=2)
    xgb_scores = cross_val_score(xgb, X, y, cv=2)
    
    print(f"RF CV Accuracy: {rf_scores.mean():.2f}")
    print(f"XGB CV Accuracy: {xgb_scores.mean():.2f}")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    os.makedirs(out_dir, exist_ok=True)
    
    rf_path = os.path.join(out_dir, "rf_model.joblib")
    xgb_path = os.path.join(out_dir, "xgb_model.joblib")
    
    joblib.dump(rf, rf_path)
    joblib.dump(xgb, xgb_path)
    
    print(f"Models saved to {out_dir}")

if __name__ == "__main__":
    train_models()
