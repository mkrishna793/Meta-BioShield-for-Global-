import json
import os
import numpy as np
from Bio import pairwise2
from bioshield.screeners.base import BaseScreener, ScreenResult
from bioshield.utils.sequence import translate_all_frames, find_orfs

# --- Fix #2: ESM-2 Protein Language Model Integration ---
# Try to import ESM-2 (Meta's protein language model).
# If not installed, we gracefully fall back to alignment-only mode.
# ESM-2 creates mathematical "shape embeddings" that can detect de novo toxins
# even when the amino acid sequence has never been seen before.
_ESM_AVAILABLE = False
try:
    import torch
    import esm
    _ESM_AVAILABLE = True
except ImportError:
    pass


class ProteinImpactScreener(BaseScreener):
    """
    Translates DNA to protein and searches against a curated database of 
    known toxins, virulence factors, and select agents to determine functional impact.
    
    Fix #2 Upgrade: When ESM-2 is available, also generates protein embeddings
    and compares them to pre-computed toxin embeddings. This catches de novo
    (brand new) toxins that share functional shape but not sequence identity.
    """
    
    def __init__(self, db_path: str, min_orf_length: int = 100, identity_threshold: float = 40.0):
        self.db_path = db_path
        self.min_orf_length = min_orf_length
        self.identity_threshold = identity_threshold
        self.toxin_db = {}
        self.esm_model = None
        self.esm_alphabet = None
        self.esm_batch_converter = None
        self.toxin_embeddings = {}  # Pre-computed ESM embeddings for known toxins
        self._load_db()
        self._init_esm()
        
    def _load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                self.toxin_db = json.load(f)
        else:
            print(f"Warning: Protein DB not found at {self.db_path}. ProteinImpactScreener will run empty.")

    def _init_esm(self):
        """Initialize ESM-2 model if available, and pre-compute toxin embeddings."""
        if not _ESM_AVAILABLE:
            return
            
        try:
            # Use the smallest ESM-2 model for speed (8M params)
            self.esm_model, self.esm_alphabet = esm.pretrained.esm2_t6_8M_UR50D()
            self.esm_batch_converter = self.esm_alphabet.get_batch_converter()
            self.esm_model.eval()
            
            # Pre-compute embeddings for all known toxins
            for accession, data in self.toxin_db.items():
                seq = data['sequence'][:1022]  # ESM max length
                emb = self._get_esm_embedding(seq)
                if emb is not None:
                    self.toxin_embeddings[accession] = emb
                    
        except Exception as e:
            print(f"ESM-2 initialization failed (falling back to alignment-only): {e}")
            self.esm_model = None

    def _get_esm_embedding(self, protein_seq: str) -> np.ndarray:
        """Get the mean-pooled ESM-2 embedding for a protein sequence."""
        if not self.esm_model:
            return None
            
        try:
            data = [("protein", protein_seq)]
            _, _, batch_tokens = self.esm_batch_converter(data)
            
            with torch.no_grad():
                results = self.esm_model(batch_tokens, repr_layers=[6])
            
            # Mean-pool over sequence length (exclude BOS/EOS tokens)
            token_representations = results["representations"][6]
            embedding = token_representations[0, 1:-1].mean(0).numpy()
            return embedding
        except Exception:
            return None

    def _esm_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Cosine similarity between two ESM-2 embeddings."""
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(emb1, emb2) / (norm1 * norm2))

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
        esm_best_match = None
        esm_highest_sim = 0.0
        
        # 1. Translate
        protein_frames = translate_all_frames(sequence)
        
        # 2. Find ORFs
        all_orfs = []
        for frame in protein_frames:
            orfs = find_orfs(frame, min_length=self.min_orf_length)
            all_orfs.extend(orfs)
            
        # 3. Traditional Alignment Search
        for orf in all_orfs:
            for accession, data in self.toxin_db.items():
                db_seq = data['sequence']
                identity = self._calculate_identity(orf, db_seq)
                
                if identity > highest_identity:
                    highest_identity = identity
                    best_match = data
        
        # 4. ESM-2 Embedding Search (Fix #2: catches de novo toxins)
        esm_used = False
        if self.esm_model and self.toxin_embeddings:
            esm_used = True
            for orf in all_orfs:
                orf_emb = self._get_esm_embedding(orf[:1022])
                if orf_emb is None:
                    continue
                    
                for accession, toxin_emb in self.toxin_embeddings.items():
                    sim = self._esm_similarity(orf_emb, toxin_emb)
                    if sim > esm_highest_sim:
                        esm_highest_sim = sim
                        esm_best_match = self.toxin_db[accession]
        
        # 5. Combine: flag if EITHER traditional alignment OR ESM embedding matches
        alignment_flagged = highest_identity >= self.identity_threshold
        esm_flagged = esm_highest_sim >= 0.85  # High threshold for embedding similarity
        is_flagged = alignment_flagged or esm_flagged
        
        # Build explanation
        if alignment_flagged and esm_flagged:
            explanation = (f"Protein match ({highest_identity:.1f}%): {best_match['name']} from {best_match['organism']}. "
                          f"IMPACT: {best_match['function']}. "
                          f"ESM-2 structural similarity ({esm_highest_sim:.2f}) confirms functional danger.")
        elif alignment_flagged:
            explanation = f"Protein match ({highest_identity:.1f}%): {best_match['name']} from {best_match['organism']}. IMPACT: {best_match['function']}"
        elif esm_flagged:
            explanation = (f"DE NOVO THREAT: No sequence alignment match, but ESM-2 protein embedding "
                          f"({esm_highest_sim:.2f} similarity) indicates functional shape resembles "
                          f"{esm_best_match['name']} from {esm_best_match['organism']}. "
                          f"IMPACT: {esm_best_match['function']}")
        else:
            mode = "alignment + ESM-2 embedding" if esm_used else "alignment only"
            explanation = f"No significant matches to known toxins or virulence factors ({mode})."
            
        return ScreenResult(
            layer_name=self.name,
            flagged=is_flagged,
            confidence=(highest_identity / 100.0) if alignment_flagged else (esm_highest_sim if esm_flagged else 1.0),
            explanation=explanation,
            details={
                "highest_identity": highest_identity,
                "matched_protein": best_match['name'] if best_match else None,
                "organism": best_match['organism'] if best_match else None,
                "function": best_match['function'] if best_match else None,
                "orfs_scanned": len(all_orfs),
                "esm2_available": esm_used,
                "esm2_highest_similarity": esm_highest_sim if esm_used else None,
                "esm2_match": esm_best_match['name'] if esm_best_match else None
            }
        )
