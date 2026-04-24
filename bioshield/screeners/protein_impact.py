import json
import os
from Bio import pairwise2
from bioshield.screeners.base import BaseScreener, ScreenResult
from bioshield.utils.sequence import translate_all_frames, find_orfs

class ProteinImpactScreener(BaseScreener):
    """
    Translates DNA to protein and searches against a curated database of 
    known toxins, virulence factors, and select agents to determine functional impact.
    """
    
    def __init__(self, db_path: str, min_orf_length: int = 100, identity_threshold: float = 40.0):
        self.db_path = db_path
        self.min_orf_length = min_orf_length
        self.identity_threshold = identity_threshold
        self.toxin_db = {}
        self._load_db()
        
    def _load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                self.toxin_db = json.load(f)
        else:
            print(f"Warning: Protein DB not found at {self.db_path}. ProteinImpactScreener will run empty.")

    def _calculate_identity(self, seq1: str, seq2: str) -> float:
        """Calculate simple percentage identity using local alignment."""
        # For a hackathon demo, we use a simple alignment. 
        # In production, this would use BLAST/DIAMOND.
        alignments = pairwise2.align.localxx(seq1, seq2)
        if not alignments:
            return 0.0
            
        best_alignment = alignments[0]
        matches = best_alignment.score
        length = min(len(seq1), len(seq2)) # Relative to the shorter sequence
        
        if length == 0:
            return 0.0
            
        return (matches / length) * 100.0

    def screen(self, sequence: str, sequence_id: str = "unknown") -> ScreenResult:
        if not self.toxin_db:
            return ScreenResult(
                layer_name=self.name,
                flagged=False,
                confidence=0.0,
                explanation="No Protein DB loaded.",
                details={"error": "db_not_found"}
            )
            
        best_match = None
        highest_identity = 0.0
        
        # 1. Translate
        protein_frames = translate_all_frames(sequence)
        
        # 2. Find ORFs
        all_orfs = []
        for frame in protein_frames:
            orfs = find_orfs(frame, min_length=self.min_orf_length)
            all_orfs.extend(orfs)
            
        # 3. Search DB
        for orf in all_orfs:
            for accession, data in self.toxin_db.items():
                db_seq = data['sequence']
                identity = self._calculate_identity(orf, db_seq)
                
                if identity > highest_identity:
                    highest_identity = identity
                    best_match = data
                    
        is_flagged = highest_identity >= self.identity_threshold
        
        if is_flagged:
            explanation = f"Protein match ({highest_identity:.1f}%): {best_match['name']} from {best_match['organism']}. IMPACT: {best_match['function']}"
        else:
            explanation = "No significant matches to known toxins or virulence factors."
            
        return ScreenResult(
            layer_name=self.name,
            flagged=is_flagged,
            confidence=(highest_identity / 100.0) if is_flagged else 1.0,
            explanation=explanation,
            details={
                "highest_identity": highest_identity,
                "matched_protein": best_match['name'] if best_match else None,
                "organism": best_match['organism'] if best_match else None,
                "function": best_match['function'] if best_match else None,
                "orfs_scanned": len(all_orfs)
            }
        )
