"""
Layer 4: Codon Bias Screener
Detects sequences that have been codon-optimized for human cell expression.
If a dangerous protein is encoded with human-preferred codons, it was engineered.
"""
from bioshield.screeners.base import BaseScreener, ScreenResult
from collections import Counter

# Human Codon Adaptation Index (CAI) weights
# Source: Homo sapiens codon usage (kazusa.or.jp), normalized per amino acid
HUMAN_CAI_WEIGHTS = {
    'TTT': 0.87, 'TTC': 1.00, 'TTA': 0.19, 'TTG': 0.33,
    'CTT': 0.33, 'CTC': 0.49, 'CTA': 0.18, 'CTG': 1.00,
    'ATT': 0.77, 'ATC': 1.00, 'ATA': 0.36, 'ATG': 1.00,
    'GTT': 0.39, 'GTC': 0.52, 'GTA': 0.25, 'GTG': 1.00,
    'TCT': 0.78, 'TCC': 0.91, 'TCA': 0.63, 'TCG': 0.23,
    'CCT': 0.88, 'CCC': 1.00, 'CCA': 0.85, 'CCG': 0.35,
    'ACT': 0.69, 'ACC': 1.00, 'ACA': 0.80, 'ACG': 0.32,
    'GCT': 0.66, 'GCC': 1.00, 'GCA': 0.57, 'GCG': 0.27,
    'TAT': 0.80, 'TAC': 1.00, 'CAT': 0.72, 'CAC': 1.00,
    'CAA': 0.36, 'CAG': 1.00, 'AAT': 0.89, 'AAC': 1.00,
    'AAA': 0.77, 'AAG': 1.00, 'GAT': 0.87, 'GAC': 1.00,
    'GAA': 0.73, 'GAG': 1.00, 'TGT': 0.84, 'TGC': 1.00,
    'TGG': 1.00, 'CGT': 0.37, 'CGC': 0.85, 'CGA': 0.51,
    'CGG': 0.93, 'AGA': 1.00, 'AGG': 0.98, 'AGT': 0.62,
    'AGC': 1.00, 'GGT': 0.49, 'GGC': 1.00, 'GGA': 0.74,
    'GGG': 0.74,
}

STOP_CODONS = {'TAA', 'TAG', 'TGA'}


class CodonBiasScreener(BaseScreener):
    """
    Computes the Codon Adaptation Index (CAI) for human cells.
    A high CAI (>threshold) means the sequence was codon-optimized
    for efficient expression in human cells — a hallmark of engineering.
    """

    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold

    def _compute_human_cai(self, seq: str) -> float:
        """Compute the Codon Adaptation Index relative to human codon usage."""
        seq = seq.upper()
        codons = [seq[i:i+3] for i in range(0, len(seq) - 2, 3)]
        codons = [c for c in codons if len(c) == 3 and c not in STOP_CODONS]

        if not codons:
            return 0.0

        import math
        log_sum = 0.0
        valid = 0
        for codon in codons:
            w = HUMAN_CAI_WEIGHTS.get(codon)
            if w and w > 0:
                log_sum += math.log(w)
                valid += 1

        if valid == 0:
            return 0.0
        return math.exp(log_sum / valid)

    def screen(self, sequence: str, sequence_id: str = "unknown") -> ScreenResult:
        if len(sequence) < 30:
            return ScreenResult(
                layer_name=self.name, flagged=False, confidence=1.0,
                explanation="Sequence too short for codon bias analysis.",
                details={"cai": 0.0}
            )

        cai = self._compute_human_cai(sequence)
        is_flagged = cai >= self.threshold

        if is_flagged:
            explanation = (f"Human Codon Adaptation Index = {cai:.3f} (threshold: {self.threshold}). "
                          f"This sequence is optimized for human cell expression — likely engineered.")
        else:
            explanation = f"Human CAI = {cai:.3f}. Normal codon usage, not optimized for human expression."

        return ScreenResult(
            layer_name=self.name, flagged=is_flagged,
            confidence=cai if is_flagged else (1.0 - cai),
            explanation=explanation,
            details={"human_cai": cai, "threshold": self.threshold}
        )
