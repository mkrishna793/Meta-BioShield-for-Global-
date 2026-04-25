"""
Layer 5: Protease Cleavage Site Screener
Scans for tiny, unalterable "activation switches" that deadly toxins
and viruses MUST have to become functional inside a human body.
An AI can scramble 10,000 letters but cannot change these 6-12 letter motifs.
"""
import re
from bioshield.screeners.base import BaseScreener, ScreenResult
from bioshield.utils.sequence import reverse_complement

# Known protease cleavage site motifs (regex patterns on protein sequence)
# These are scanned against all 6 reading frames of the input DNA.
CLEAVAGE_MOTIFS = {
    "Furin (polybasic)": {
        "pattern": r'R.[KR]R',
        "risk": "HIGH",
        "context": "Furin cleavage enables viral entry (e.g. SARS-CoV-2 spike protein)."
    },
    "Furin (RRAR)": {
        "pattern": r'RRAR',
        "risk": "CRITICAL",
        "context": "Polybasic furin site — hallmark of enhanced pandemic potential."
    },
    "Furin (PRRA insert)": {
        "pattern": r'PRRA',
        "risk": "CRITICAL",
        "context": "PRRA insertion — matches the SARS-CoV-2 gain-of-function signature."
    },
    "Thrombin": {
        "pattern": r'LVPR[GS]',
        "risk": "MEDIUM",
        "context": "Thrombin cleavage site used in recombinant protein engineering."
    },
    "TEV protease": {
        "pattern": r'ENLYFQ[SG]',
        "risk": "MEDIUM",
        "context": "TEV cleavage — common in lab-engineered constructs."
    },
    "Enterokinase": {
        "pattern": r'DDDDK',
        "risk": "MEDIUM",
        "context": "Enterokinase site — recombinant protein processing marker."
    },
    "Factor Xa": {
        "pattern": r'I[ED]GR',
        "risk": "MEDIUM",
        "context": "Factor Xa cleavage — used in engineered fusion proteins."
    },
    "Anthrax PA cleavage": {
        "pattern": r'RKKR',
        "risk": "CRITICAL",
        "context": "Anthrax protective antigen furin activation site."
    },
}


class CleavageSiteScreener(BaseScreener):
    """
    Scans DNA (translated in all 6 frames) for protease cleavage site motifs.
    These are the tiny molecular "switches" that activate toxins and viruses.
    """

    def __init__(self, min_risk_level: str = "MEDIUM"):
        self.min_risk_level = min_risk_level
        self._risk_order = {"MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

    def screen(self, sequence: str, sequence_id: str = "unknown") -> ScreenResult:
        if len(sequence) < 15:
            return ScreenResult(
                layer_name=self.name, flagged=False, confidence=1.0,
                explanation="Sequence too short for cleavage site analysis.",
                details={"matches": []}
            )

        from bioshield.utils.sequence import translate_all_frames

        # Translate all 6 reading frames
        protein_frames = translate_all_frames(sequence)

        matches = []
        highest_risk = 0

        for frame_idx, protein in enumerate(protein_frames):
            for motif_name, motif_data in CLEAVAGE_MOTIFS.items():
                if self._risk_order.get(motif_data["risk"], 0) < self._risk_order.get(self.min_risk_level, 0):
                    continue

                found = list(re.finditer(motif_data["pattern"], protein))
                if found:
                    risk_val = self._risk_order.get(motif_data["risk"], 0)
                    if risk_val > highest_risk:
                        highest_risk = risk_val
                    matches.append({
                        "motif": motif_name,
                        "risk": motif_data["risk"],
                        "context": motif_data["context"],
                        "frame": frame_idx,
                        "count": len(found)
                    })

        is_flagged = len(matches) > 0

        if is_flagged:
            critical = [m for m in matches if m["risk"] == "CRITICAL"]
            if critical:
                top = critical[0]
                explanation = (f"CRITICAL cleavage site detected: {top['motif']} "
                              f"({top['count']}x in frame {top['frame']}). {top['context']}")
            else:
                top = matches[0]
                explanation = (f"Cleavage site detected: {top['motif']} ({top['risk']}). "
                              f"{top['context']}")
        else:
            explanation = f"No protease cleavage sites found ({len(CLEAVAGE_MOTIFS)} motifs checked)."

        return ScreenResult(
            layer_name=self.name, flagged=is_flagged,
            confidence=(highest_risk / 3.0) if is_flagged else 1.0,
            explanation=explanation,
            details={"matches": matches, "total_motifs_checked": len(CLEAVAGE_MOTIFS)}
        )
