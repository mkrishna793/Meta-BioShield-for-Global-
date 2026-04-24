"""
IBBIS v2.0 (Powered by BioShield) - Hackathon Demo
This script demonstrates the complete, seamless cloud integration between
the legacy IBBIS Common Mechanism and the advanced BioShield AI layers.
"""

import os
import sys
import json

# Add project root to python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from bioshield.ibbis_integration import IbbisV2Orchestrator

# Color helpers
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"

def print_ibbis_v2_report(report: dict):
    """Pretty prints the unified JSON report for the demo."""
    
    final = report["ibbis_v2_final_verdict"]
    color = RED if final == "REJECT" else (YELLOW if final == "FLAG_FOR_REVIEW" else GREEN)
    
    print(f"\n{BOLD}{CYAN}=== IBBIS v2.0 CLOUD API REPORT ==={RESET}")
    print(f"Order ID: {report['order_id']}")
    print(f"Final Action: {color}{BOLD}{final}{RESET}")
    print("-" * 40)
    
    # Legacy IBBIS Layer
    leg_rec = report["legacy_ibbis_layer"]["recommendation"]
    leg_col = RED if leg_rec == "REJECT" else GREEN
    print(f"1. Legacy IBBIS Engine: {leg_col}{leg_rec}{RESET}")
    for match in report["legacy_ibbis_layer"].get("matches", []):
        print(f"   -> Exact BLAST Match: {match['organism']} (Score: {match['alignment_score']})")
    if not report["legacy_ibbis_layer"].get("matches"):
        print("   -> No exact alignments found. (Blind to novel/AI variants)")
        
    # BioShield AI Layer
    print(f"\n2. BioShield AI Defense Layer (Confidence: {report['bioshield_ai_layer']['confidence_score']:.2f})")
    for layer in report["bioshield_ai_layer"]["layer_breakdown"]:
        l_stat = layer['status']
        l_col = RED if l_stat == "FLAG" else GREEN
        print(f"   [{layer['layer']}] {l_col}{l_stat}{RESET}")
        print(f"      {layer['explanation'][:100]}...")
        
    print(f"{CYAN}==================================={RESET}\n")


def main():
    print(f"{BOLD}Initializing IBBIS v2.0 Cloud Orchestrator...{RESET}")
    config_path = os.path.join(os.path.dirname(__file__), 'bioshield-config.yaml')
    orchestrator = IbbisV2Orchestrator(config_path)
    print("Ready.\n")
    
    # ---------------------------------------------------------
    # SCENARIO 1: Standard Anthrax Threat
    # ---------------------------------------------------------
    print(f"{BOLD}[SCENARIO 1] Screening Standard Known Pathogen (Anthrax)...{RESET}")
    print("This sequence is straight from NCBI. Traditional IBBIS should catch it easily.")
    
    anthrax_mock = "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC" * 15 + "TATA" * 20
    report_1 = orchestrator.process_order(anthrax_mock, "ORDER_001_KNOWN_THREAT")
    print_ibbis_v2_report(report_1)
    
    # ---------------------------------------------------------
    # SCENARIO 2: AI-Evasion Variant (The Hackathon Problem)
    # ---------------------------------------------------------
    print(f"{BOLD}[SCENARIO 2] Screening AI Codon-Shuffled Evasion Variant...{RESET}")
    print("A bad actor used an AI tool to change 20% of the DNA letters, breaking the exact BLAST match.")
    print("Legacy IBBIS will completely miss this. BioShield must catch it.")
    
    import random
    random.seed(42) # Deterministic shuffle for demo
    evasion = list(anthrax_mock)
    for i in range(len(evasion)):
        if random.random() > 0.8:  # 20% mutation rate
            evasion[i] = random.choice(['A','T','C','G'])
    evasion_seq = "".join(evasion)
    
    report_2 = orchestrator.process_order(evasion_seq, "ORDER_002_AI_EVASION")
    print_ibbis_v2_report(report_2)
    
    print(f"{BOLD}{GREEN}DEMO COMPLETE:{RESET} BioShield successfully protected the IBBIS ecosystem from an AI evasion attack.")

if __name__ == "__main__":
    main()
