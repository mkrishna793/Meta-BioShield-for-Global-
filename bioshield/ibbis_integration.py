import json
import logging
from typing import Dict, Any, List

from bioshield.pipeline import BioShieldPipeline
from bioshield.screeners.base import Verdict, ScreenResult, FinalVerdict

logger = logging.getLogger("IBBIS_v2")

class MockLegacyIBBIS:
    """
    Simulates the JSON output of the legacy IBBIS 'commec' tool.
    Legacy IBBIS relies on exact BLAST/HMM alignments. It catches standard threats
    but FAILS to catch sequences where the codons have been shuffled by AI.
    """
    def __init__(self):
        self.known_signatures = {
            "anthrax_mock": "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC",
            "ebola_mock": "CGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTA"
        }

    def screen(self, sequence: str, seq_id: str) -> Dict[str, Any]:
        """Simulate a BLAST/HMM alignment search."""
        sequence = sequence.upper()
        
        # Check for exact matches (The old way of screening)
        for name, sig in self.known_signatures.items():
            if sig in sequence:
                return {
                    "tool": "IBBIS_commec_legacy",
                    "status": "THREAT_DETECTED",
                    "matches": [
                        {
                            "database": "ncbi_nr",
                            "organism": name.split('_')[0].capitalize(),
                            "alignment_score": 100.0,
                            "e_value": 0.0001
                        }
                    ],
                    "recommendation": "REJECT"
                }
                
        # If no EXACT match is found (e.g. AI codon-shuffled it), IBBIS says it's safe
        return {
            "tool": "IBBIS_commec_legacy",
            "status": "CLEAR",
            "matches": [],
            "recommendation": "PASS"
        }

class IbbisV2Orchestrator:
    """
    The Master Cloud Connector: IBBIS v2.0
    Combines legacy IBBIS JSON output with the advanced BioShield AI layers.
    """
    def __init__(self, bioshield_config_path: str):
        self.legacy_ibbis = MockLegacyIBBIS()
        self.bioshield = BioShieldPipeline(bioshield_config_path)

    def process_order(self, sequence: str, order_id: str) -> Dict[str, Any]:
        """Process an incoming DNA synthesis order through both systems."""
        
        # 1. Run Legacy IBBIS (Simulated Server Call)
        legacy_report = self.legacy_ibbis.screen(sequence, order_id)
        
        # 2. Run BioShield (The AI-Defense Upgrade)
        bioshield_verdict: FinalVerdict = self.bioshield.screen_sequence(sequence, order_id)
        
        # 3. The Master Verdict Engine (Merging them)
        # If EITHER system rejects it, it is rejected.
        final_decision = "PASS"
        if legacy_report["recommendation"] == "REJECT" or bioshield_verdict.verdict == Verdict.REJECT:
            final_decision = "REJECT"
        elif bioshield_verdict.verdict == Verdict.FLAG:
            final_decision = "FLAG_FOR_REVIEW"
            
        # 4. Generate the Unified "IBBIS v2.0" JSON Report
        unified_report = {
            "order_id": order_id,
            "ibbis_v2_final_verdict": final_decision,
            "legacy_ibbis_layer": legacy_report,
            "bioshield_ai_layer": {
                "confidence_score": bioshield_verdict.confidence,
                "layer_breakdown": [
                    {
                        "layer": r.layer_name,
                        "status": "FLAG" if r.flagged else "PASS",
                        "explanation": r.explanation
                    } for r in bioshield_verdict.per_layer_results
                ]
            }
        }
        
        return unified_report
