import json
import os
import numpy as np
from itertools import product
from bioshield.screeners.base import BaseScreener, ScreenResult
from bioshield.utils.sequence import extract_kmers, kmer_frequency_vector, cosine_similarity

class KmerScreener(BaseScreener):
    """
    Screens sequences using K-mer fingerprinting to detect heavily mutated 
    or codon-optimized pathogen sequences (AI-evasion resistance).
    """
    
    def __init__(self, db_path: str, threshold: float = 0.85):
        self.db_path = db_path
        self.threshold = threshold
        self.threat_profiles = {}
        self.vocabs = {}
        self._load_db()
        self._build_vocabs()
        
    def _build_vocabs(self):
        """Build standard vocabularies for k=3,4,5,6 to ensure vector alignment."""
        bases = ['A', 'C', 'G', 'T']
        for k in [3, 4, 5, 6]:
            # Generate all possible k-mers alphabetically
            self.vocabs[str(k)] = [''.join(p) for p in product(bases, repeat=k)]

    def _load_db(self):
        """Load pre-computed threat k-mer profiles."""
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                self.threat_profiles = json.load(f)
        else:
            print(f"Warning: Threat DB not found at {self.db_path}. KmerScreener will run empty.")
            self.threat_profiles = {}

    def screen(self, sequence: str, sequence_id: str = "unknown") -> ScreenResult:
        if not self.threat_profiles:
            return ScreenResult(
                layer_name=self.name,
                flagged=False,
                confidence=0.0,
                explanation="No threat DB loaded.",
                details={"error": "db_not_found"}
            )
            
        best_match_organism = None
        max_similarity = 0.0
        best_k = None
        
        # Test k=4, 5, 6 (k=3 is usually too short for specific organism signatures, but good for GC bias)
        ks_to_test = [4, 5, 6]
        
        for organism, profiles in self.threat_profiles.items():
            for k in ks_to_test:
                k_str = str(k)
                if k_str not in profiles:
                    continue
                    
                # Convert the stored profile dictionary back to an aligned vector
                threat_profile_dict = profiles[k_str]
                vocab = self.vocabs[k_str]
                
                # Threat vector
                threat_vec = np.array([threat_profile_dict.get(v, 0.0) for v in vocab], dtype=float)
                
                # Input vector
                input_vec = kmer_frequency_vector(sequence, k, vocab=vocab)
                
                sim = cosine_similarity(input_vec, threat_vec)
                
                if sim > max_similarity:
                    max_similarity = sim
                    best_match_organism = organism
                    best_k = k
                    
        is_flagged = max_similarity >= self.threshold
        
        if is_flagged:
            explanation = f"K-mer fingerprint match ({max_similarity:.2f}) with {best_match_organism} at k={best_k}. Potential evasion variant."
        else:
            explanation = "No significant k-mer threat signature found."
            
        return ScreenResult(
            layer_name=self.name,
            flagged=is_flagged,
            confidence=max_similarity if max_similarity > 0 else 1.0, # high confidence if no match at all
            explanation=explanation,
            details={
                "max_similarity": max_similarity,
                "best_match_organism": best_match_organism,
                "best_k": best_k,
                "threshold_used": self.threshold
            }
        )
