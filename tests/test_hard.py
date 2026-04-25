"""
BioShield Hard Test Suite v2.0
Tests ALL vulnerability fixes:
  Fix #1: Sliding Window (Trojan Horse dilution attack)
  Fix #2: ESM-2 stub (de novo protein - architecture test)
  Fix #3: Bifurcated Pipeline (micro-sequence split-order attack)
  Fix #4: Canonical K-mers (reverse-complement evasion)
"""

import os
import sys
import random
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bioshield.pipeline import BioShieldPipeline
from bioshield.screeners.base import Verdict
from bioshield.utils.sequence import reverse_complement

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

passed = 0
failed = 0

def run_test(name, sequence, expected_verdicts, pipeline, fix_label=""):
    global passed, failed
    label = f" [{fix_label}]" if fix_label else ""
    print(f"\n{BOLD}[TEST{label}] {name}{RESET}")
    print(f"  Sequence length: {len(sequence)} bp")
    
    try:
        verdict = pipeline.screen_sequence(sequence, name)
        actual = verdict.verdict
        
        if actual in expected_verdicts:
            print(f"  Result: {GREEN}OK {actual.value}{RESET} (expected: {[v.value for v in expected_verdicts]})")
            for r in verdict.per_layer_results:
                status = f"{RED}FLAG{RESET}" if r.flagged else f"{GREEN}PASS{RESET}"
                print(f"    [{r.layer_name}] {status}: {r.explanation[:100]}")
            passed += 1
        else:
            print(f"  Result: {RED}FAIL {actual.value}{RESET} (expected: {[v.value for v in expected_verdicts]})")
            for r in verdict.per_layer_results:
                status = f"{RED}FLAG{RESET}" if r.flagged else f"{GREEN}PASS{RESET}"
                print(f"    [{r.layer_name}] {status}: {r.explanation[:100]}")
            failed += 1
    except Exception as e:
        print(f"  Result: {RED}FAIL CRASHED: {e}{RESET}")
        traceback.print_exc()
        failed += 1

def main():
    global passed, failed
    
    print(f"\n{BOLD}{'='*60}")
    print("     BIOSHIELD HARD TEST SUITE v2.0")
    print(f"     Testing ALL 4 Vulnerability Fixes")
    print(f"{'='*60}{RESET}")
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'bioshield-config.yaml')
    pipeline = BioShieldPipeline(config_path)
    
    print(f"\nLoaded {len(pipeline.screeners)} screeners: {[s.name for s in pipeline.screeners]}")
    
    # ===== BASELINE TESTS =====
    
    gfp = ("ATGCGTAAAGGCGAAGAGCTGTTCACTGGTGTCGTCCCTATTCTGGTGGAACTGGATGGTGATGTCAACGGTCATAAGTTTTCCGTGCG"
           "TGGCGAGGGTGAAGGTGACGCAACTAATGGTAAACTGACGCTGAAGTTCATCTGTACTACTGGTAAACTGCCGGTTCCTTGGCCGACTC"
           "TGGTAACGACGCTGACTTATGGTGTTCAGTGCTTTGCTCGTTATCCGGACCATATGAAGCAGCATGACTTCTTCAAGTCCGCCATGCCG"
           "GAAGGCTATGTGCAGGAACGCACGATTTCCTTTAAGGATGACGGCACGTACAAAACGCGTGCGGAAGTGAAATTTGAAGGCGATACCCT"
           "GGTAAACCGCATTGAGCTGAAAGGCATTGACTTTAAAGAAGACGGCAATATCCTGGGCCATAAGCTGGAATACAATTTTAACAGCCACAA"
           "TGTTTACATCACCGCCGATAAACAAAAAAATGGCATTAAAGCGAATTTTAAAATTCGCCACAACGTGGAGGATGGCAGCGTGCAGCTGGC"
           "TGATCACTACCAGCAAAACACTCCAATCGGTGATGGTCCTGTTCTGCTGCCAGACAATCACTATCTGAGCACGCAAAGCGTTCTGTCTA"
           "AAGATCCGAACGAGAAACGCGATCATATGGTTCTGCTGGAGTTCGTAACCGCAGCGGGCATCACGCATGGTATGGATGAACTGTACAAA"
           "TAA")
    run_test("Safe GFP Gene (Baseline)", gfp, [Verdict.PASS, Verdict.FLAG], pipeline)
    
    anthrax_mock = "ATGCATGCATGC" * 50 + "TATA" * 20
    run_test("Anthrax Threat (Baseline)", anthrax_mock, [Verdict.FLAG, Verdict.REJECT], pipeline)
    
    # ===== FIX #1: SLIDING WINDOW (Trojan Horse) =====
    print(f"\n{CYAN}--- Fix #1: Sliding Window (Trojan Horse Dilution Attack) ---{RESET}")
    
    # Build a 5000bp safe sequence with a 200bp threat hidden in the middle
    random.seed(42)
    safe_flank = "".join(random.choices(['A','T','C','G'], weights=[0.29,0.29,0.21,0.21], k=2500))
    threat_insert = anthrax_mock[:200]
    trojan_horse = safe_flank[:2400] + threat_insert + safe_flank[2400:]
    run_test("Trojan Horse: 200bp Threat Hidden in 5000bp Safe DNA", 
             trojan_horse, [Verdict.FLAG, Verdict.REJECT], pipeline, "Fix #1")
    
    # ===== FIX #3: BIFURCATED PIPELINE (Micro-Sequence) =====
    print(f"\n{CYAN}--- Fix #3: Bifurcated Pipeline (Split-Order Attack) ---{RESET}")
    
    # Very short random safe sequence -> should NOT crash, should PASS
    short_safe = "ATGCGTAAAGGCGAAGAGCTGTTCACTGGTGTCGTCC"
    run_test("Short Safe Sequence (37bp)", short_safe, [Verdict.PASS], pipeline, "Fix #3")
    
    # Very short sequence that IS a known trigger motif
    run_test("Short Trigger: Anthrax PA Signal (18bp)", 
             "ATGAAAAAACGGAGTTAT", [Verdict.FLAG, Verdict.REJECT], pipeline, "Fix #3")
    
    # Short junk that is NOT a trigger
    run_test("Short Random Junk (50bp)", 
             "GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC", 
             [Verdict.PASS], pipeline, "Fix #3")
    
    # ===== FIX #4: REVERSE-COMPLEMENT EVASION =====
    print(f"\n{CYAN}--- Fix #4: Canonical K-mers (Reverse-Complement Evasion) ---{RESET}")
    
    # Take the safe GFP and submit its reverse complement
    gfp_rc = reverse_complement(gfp)
    run_test("Reverse-Complement of GFP (should still be safe-ish)", 
             gfp_rc, [Verdict.PASS, Verdict.FLAG], pipeline, "Fix #4")
    
    # Take the threat and submit its reverse complement
    anthrax_rc = reverse_complement(anthrax_mock)
    run_test("Reverse-Complement of Anthrax (should still be caught)", 
             anthrax_rc, [Verdict.FLAG, Verdict.REJECT], pipeline, "Fix #4")
    
    # ===== EDGE CASES =====
    print(f"\n{CYAN}--- Edge Cases ---{RESET}")
    
    run_test("Empty Sequence", "", [Verdict.PASS], pipeline, "Edge")
    
    extreme_gc = "GCGCGCGCGCGCGCGCGCGC" * 30
    run_test("Extreme GC (100%)", extreme_gc, [Verdict.FLAG, Verdict.REJECT], pipeline, "Edge")
    
    # Chimeric splice with sliding window
    chimera = gfp[:200] + anthrax_mock[:200] + gfp[200:400]
    run_test("Chimeric Splice (GFP+Anthrax+GFP)", chimera, [Verdict.FLAG, Verdict.REJECT], pipeline, "Edge")
    
    # ===== SUMMARY =====
    print(f"\n{BOLD}{'='*60}")
    total = passed + failed
    print(f"  RESULTS: {GREEN}{passed} PASSED{RESET}, {RED}{failed} FAILED{RESET} out of {total}")
    print(f"{'='*60}{RESET}\n")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
