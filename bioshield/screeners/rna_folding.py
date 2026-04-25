"""
Layer 6: RNA Secondary Structure Screener
Analyzes the folding potential of RNA transcribed from the input DNA.
Dangerous viruses rely on specific RNA 3D shapes (hairpins, loops) to replicate.
If AI shuffles codons, it often preserves or must preserve these structures.

Uses ViennaRNA if installed; falls back to a palindrome-density heuristic.
"""
import re
from bioshield.screeners.base import BaseScreener, ScreenResult

_VIENNA_AVAILABLE = False
try:
    import RNA
    _VIENNA_AVAILABLE = True
except ImportError:
    pass

# Known viral MFE (Minimum Free Energy) ranges per kilobase
# More negative = more stable folding = more structured RNA
VIRAL_MFE_RANGES = {
    "SARS-CoV-2": (-35, -25),   # kcal/mol per kb
    "Ebola":      (-30, -20),
    "HIV":        (-40, -30),
    "Influenza":  (-25, -15),
}


class RNAFoldingScreener(BaseScreener):
    """
    Screens for suspicious RNA secondary structure patterns.
    
    When ViennaRNA is available: computes actual Minimum Free Energy (MFE)
    and compares to known viral RNA stability profiles.
    
    Fallback: Estimates folding potential using palindromic stem density
    (regions that can form hairpin structures) and GC bond stability.
    """

    def __init__(self, palindrome_threshold: float = 0.15):
        self.palindrome_threshold = palindrome_threshold
        self.use_vienna = _VIENNA_AVAILABLE

    def _transcribe(self, dna: str) -> str:
        """Convert DNA to RNA (T -> U)."""
        return dna.upper().replace('T', 'U')

    def _vienna_mfe(self, rna: str) -> float:
        """Compute MFE using ViennaRNA library."""
        structure, mfe = RNA.fold(rna[:2000])  # Limit length for speed
        return mfe

    def _palindrome_density(self, seq: str) -> float:
        """
        Estimate RNA hairpin-forming potential by counting palindromic stems.
        A palindromic stem is where a short subsequence has its reverse complement
        nearby, allowing the RNA to fold back on itself.
        """
        seq = seq.upper()
        complement = str.maketrans('ACGU', 'UGCA')
        stem_count = 0
        stem_len = 6  # Minimum stem length for a stable hairpin
        window = 50   # Search window for the complement

        for i in range(len(seq) - stem_len - 4):
            stem = seq[i:i+stem_len]
            rc_stem = stem.translate(complement)[::-1]
            # Look for the reverse complement within the window ahead
            search_region = seq[i+stem_len+3:i+stem_len+3+window]
            if rc_stem in search_region:
                stem_count += 1

        density = stem_count / max(1, len(seq) - stem_len)
        return density

    def _gc_stability(self, seq: str) -> float:
        """Higher GC content = more stable RNA folds (3 hydrogen bonds vs 2)."""
        seq = seq.upper()
        gc = seq.count('G') + seq.count('C')
        return gc / max(1, len(seq))

    def screen(self, sequence: str, sequence_id: str = "unknown") -> ScreenResult:
        if len(sequence) < 50:
            return ScreenResult(
                layer_name=self.name, flagged=False, confidence=1.0,
                explanation="Sequence too short for RNA folding analysis.",
                details={"mode": "skipped"}
            )

        rna = self._transcribe(sequence)

        if self.use_vienna:
            # Full ViennaRNA MFE analysis
            mfe = self._vienna_mfe(rna)
            mfe_per_kb = (mfe / len(rna)) * 1000

            # Check if MFE falls in known viral ranges
            viral_match = None
            for virus, (low, high) in VIRAL_MFE_RANGES.items():
                if low <= mfe_per_kb <= high:
                    viral_match = virus
                    break

            is_flagged = viral_match is not None or mfe_per_kb < -20
            explanation = (f"RNA MFE = {mfe:.1f} kcal/mol ({mfe_per_kb:.1f}/kb). "
                          f"ViennaRNA analysis: {'matches ' + viral_match + ' stability profile' if viral_match else 'no viral match'}.")

            return ScreenResult(
                layer_name=self.name, flagged=is_flagged,
                confidence=abs(mfe_per_kb) / 50.0 if is_flagged else 1.0,
                explanation=explanation,
                details={"mfe": mfe, "mfe_per_kb": mfe_per_kb, "viral_match": viral_match, "mode": "vienna"}
            )
        else:
            # Fallback: palindrome density heuristic
            pal_density = self._palindrome_density(rna)
            gc_stab = self._gc_stability(rna)
            
            # Combined folding score: high palindrome density + high GC = structured RNA
            fold_score = (pal_density * 0.7) + (gc_stab * 0.3)
            is_flagged = pal_density >= self.palindrome_threshold

            if is_flagged:
                explanation = (f"High RNA hairpin density ({pal_density:.3f}, threshold: {self.palindrome_threshold}). "
                              f"GC stability: {gc_stab:.2f}. Structured RNA suggests functional viral genome.")
            else:
                explanation = (f"RNA palindrome density = {pal_density:.3f} (low). "
                              f"No unusual secondary structure detected (heuristic mode).")

            return ScreenResult(
                layer_name=self.name, flagged=is_flagged,
                confidence=fold_score if is_flagged else 1.0,
                explanation=explanation,
                details={"palindrome_density": pal_density, "gc_stability": gc_stab, 
                         "fold_score": fold_score, "mode": "heuristic"}
            )
