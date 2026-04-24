from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class Verdict(Enum):
    PASS = "PASS"        # All layers clear
    FLAG = "FLAG"        # 1-2 layers flagged, human review needed
    REJECT = "REJECT"    # 3+ layers flagged, auto-reject

@dataclass
class ScreenResult:
    """Result from a single screening layer"""
    layer_name: str
    flagged: bool
    confidence: float
    explanation: str
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FinalVerdict:
    """Aggregated final verdict for a sequence"""
    sequence_id: str
    verdict: Verdict
    confidence: float
    per_layer_results: List[ScreenResult]
    audit_trail: List[str]

class BaseScreener:
    """Abstract base class for all BioShield screening layers."""
    
    @property
    def name(self) -> str:
        return self.__class__.__name__

    def screen(self, sequence: str, sequence_id: str = "unknown") -> ScreenResult:
        """
        Screen a single DNA sequence.
        
        Args:
            sequence: The raw DNA sequence string (A, T, C, G)
            sequence_id: Identifier for the sequence
            
        Returns:
            ScreenResult object with the screening outcome
        """
        raise NotImplementedError("Subclasses must implement screen()")

class VerdictEngine:
    """Aggregates results from multiple screeners to produce a final verdict."""
    
    @staticmethod
    def aggregate(sequence_id: str, results: List[ScreenResult]) -> FinalVerdict:
        flags = sum(1 for r in results if r.flagged)
        
        if flags == 0:
            verdict = Verdict.PASS
        elif flags <= 2:
            verdict = Verdict.FLAG
        else:
            verdict = Verdict.REJECT
            
        # Overall confidence is an average of the layer confidences
        if results:
            avg_confidence = sum(r.confidence for r in results) / len(results)
        else:
            avg_confidence = 1.0
            
        audit_trail = [
            f"[{r.layer_name}] {'FLAGGED' if r.flagged else 'PASSED'}: {r.explanation}"
            for r in results
        ]
        
        return FinalVerdict(
            sequence_id=sequence_id,
            verdict=verdict,
            confidence=avg_confidence,
            per_layer_results=results,
            audit_trail=audit_trail
        )
