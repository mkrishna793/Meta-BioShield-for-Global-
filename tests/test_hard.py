"""
BioShield Hard Test Suite
Tests the full pipeline against real-world scenarios:
  1. Known safe lab gene (GFP) -> must PASS
  2. Known threat signature (Anthrax k-mer match) -> must FLAG/REJECT
  3. AI-evasion variant (codon-shuffled threat) -> must FLAG/REJECT
  4. Short random junk -> must PASS (no false positives on noise)
  5. Edge case: empty/very short sequence -> must not crash
"""

import os
import sys
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bioshield.pipeline import BioShieldPipeline
from bioshield.screeners.base import Verdict

# Color helpers
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

passed = 0
failed = 0

def run_test(name, sequence, expected_verdicts, pipeline):
    """Run a single test case."""
    global passed, failed
    print(f"\n{BOLD}[TEST] {name}{RESET}")
    print(f"  Sequence length: {len(sequence)} bp")
    
    try:
        verdict = pipeline.screen_sequence(sequence, name)
        actual = verdict.verdict
        
        if actual in expected_verdicts:
            print(f"  Result: {GREEN}OK {actual.value}{RESET} (expected: {[v.value for v in expected_verdicts]})")
            for r in verdict.per_layer_results:
                status = f"{RED}FLAG{RESET}" if r.flagged else f"{GREEN}PASS{RESET}"
                print(f"    [{r.layer_name}] {status}: {r.explanation[:80]}")
            passed += 1
        else:
            print(f"  Result: {RED}FAIL {actual.value}{RESET} (expected: {[v.value for v in expected_verdicts]})")
            for r in verdict.per_layer_results:
                status = f"{RED}FLAG{RESET}" if r.flagged else f"{GREEN}PASS{RESET}"
                print(f"    [{r.layer_name}] {status}: {r.explanation[:80]}")
            failed += 1
    except Exception as e:
        print(f"  Result: {RED}FAIL CRASHED: {e}{RESET}")
        traceback.print_exc()
        failed += 1

def main():
    global passed, failed
    
    print(f"\n{BOLD}{'='*60}")
    print("     BIOSHIELD HARD TEST SUITE")
    print(f"{'='*60}{RESET}")
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'bioshield-config.yaml')
    pipeline = BioShieldPipeline(config_path)
    
    print(f"\nLoaded {len(pipeline.screeners)} screeners: {[s.name for s in pipeline.screeners]}")
    
    # -------------------------------------------------------
    # TEST 1: Known safe lab gene (GFP)
    # -------------------------------------------------------
    gfp = ("ATGCGTAAAGGCGAAGAGCTGTTCACTGGTGTCGTCCCTATTCTGGTGGAACTGGATGGTGATGTCAACGGTCATAAGTTTTCCGTGCG"
           "TGGCGAGGGTGAAGGTGACGCAACTAATGGTAAACTGACGCTGAAGTTCATCTGTACTACTGGTAAACTGCCGGTTCCTTGGCCGACTC"
           "TGGTAACGACGCTGACTTATGGTGTTCAGTGCTTTGCTCGTTATCCGGACCATATGAAGCAGCATGACTTCTTCAAGTCCGCCATGCCG"
           "GAAGGCTATGTGCAGGAACGCACGATTTCCTTTAAGGATGACGGCACGTACAAAACGCGTGCGGAAGTGAAATTTGAAGGCGATACCCT"
           "GGTAAACCGCATTGAGCTGAAAGGCATTGACTTTAAAGAAGACGGCAATATCCTGGGCCATAAGCTGGAATACAATTTTAACAGCCACAA"
           "TGTTTACATCACCGCCGATAAACAAAAAAATGGCATTAAAGCGAATTTTAAAATTCGCCACAACGTGGAGGATGGCAGCGTGCAGCTGGC"
           "TGATCACTACCAGCAAAACACTCCAATCGGTGATGGTCCTGTTCTGCTGCCAGACAATCACTATCTGAGCACGCAAAGCGTTCTGTCTA"
           "AAGATCCGAACGAGAAACGCGATCATATGGTTCTGCTGGAGTTCGTAACCGCAGCGGGCATCACGCATGGTATGGATGAACTGTACAAA"
           "TAA")
    run_test("Safe GFP Gene", gfp, [Verdict.PASS, Verdict.FLAG], pipeline)
    
    # -------------------------------------------------------
    # TEST 2: Known threat (Anthrax k-mer signature match)
    # -------------------------------------------------------
    anthrax_mock = "ATGCATGCATGC" * 50 + "TATA" * 20
    run_test("Anthrax Threat Signature", anthrax_mock, [Verdict.FLAG, Verdict.REJECT], pipeline)
    
    # -------------------------------------------------------
    # TEST 3: AI-evasion variant (codon-shuffled threat)
    # -------------------------------------------------------
    import random
    random.seed(42)
    evasion = list(anthrax_mock)
    for i in range(len(evasion)):
        if random.random() > 0.8:
            evasion[i] = random.choice(['A','T','C','G'])
    evasion_seq = "".join(evasion)
    run_test("AI-Evasion Codon-Shuffled Variant", evasion_seq, [Verdict.FLAG, Verdict.REJECT], pipeline)
    
    # -------------------------------------------------------
    # TEST 4: Short random junk (should NOT trigger false positive)
    # -------------------------------------------------------
    random.seed(99)
    junk = "".join(random.choices(['A','T','C','G'], k=150))
    run_test("Short Random Junk (150bp)", junk, [Verdict.PASS, Verdict.FLAG], pipeline)
    
    # -------------------------------------------------------
    # TEST 5: Long random safe sequence (natural-looking DNA)
    # -------------------------------------------------------
    random.seed(77)
    safe_long = "".join(random.choices(['A','T','C','G'], weights=[0.29, 0.29, 0.21, 0.21], k=1500))
    run_test("Long Random Safe (1500bp, natural GC)", safe_long, [Verdict.PASS, Verdict.FLAG], pipeline)
    
    # -------------------------------------------------------
    # TEST 6: Edge case — very short sequence
    # -------------------------------------------------------
    run_test("Edge Case: Very Short (20bp)", "ATGCATGCATGCATGCATGC", [Verdict.PASS, Verdict.FLAG], pipeline)
    
    # -------------------------------------------------------
    # TEST 7: Edge case — extreme GC content (engineered DNA signal)
    # -------------------------------------------------------
    high_gc = "GCGCGCGCGCGCGCGCGCGC" * 30
    run_test("Extreme High GC Content (100% GC)", high_gc, [Verdict.FLAG, Verdict.REJECT], pipeline)
    
    # -------------------------------------------------------
    # TEST 8: Chimeric sequence (safe + threat spliced)
    # -------------------------------------------------------
    chimera = gfp[:200] + anthrax_mock[:200] + gfp[200:400]
    run_test("Chimeric Splice (GFP + Anthrax + GFP)", chimera, [Verdict.FLAG, Verdict.REJECT], pipeline)
    
    # -------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------
    print(f"\n{BOLD}{'='*60}")
    print(f"  RESULTS: {GREEN}{passed} PASSED{RESET}, {RED}{failed} FAILED{RESET} out of {passed + failed}")
    print(f"{'='*60}{RESET}\n")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
