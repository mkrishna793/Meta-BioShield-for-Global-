"""
BioShield Hard Test Suite v3.0 — 6-Layer Defense-in-Depth
Tests all vulnerability fixes + 3 new biological screeners.
"""
import os, sys, random, traceback
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bioshield.pipeline import BioShieldPipeline
from bioshield.screeners.base import Verdict
from bioshield.utils.sequence import reverse_complement

GREEN, RED, YELLOW, CYAN, RESET, BOLD = "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[0m", "\033[1m"
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
            print(f"  Result: {GREEN}OK {actual.value}{RESET}")
            for r in verdict.per_layer_results:
                status = f"{RED}FLAG{RESET}" if r.flagged else f"{GREEN}PASS{RESET}"
                print(f"    [{r.layer_name}] {status}: {r.explanation[:90]}")
            passed += 1
        else:
            print(f"  Result: {RED}FAIL {actual.value}{RESET} (expected: {[v.value for v in expected_verdicts]})")
            for r in verdict.per_layer_results:
                status = f"{RED}FLAG{RESET}" if r.flagged else f"{GREEN}PASS{RESET}"
                print(f"    [{r.layer_name}] {status}: {r.explanation[:90]}")
            failed += 1
    except Exception as e:
        print(f"  Result: {RED}CRASH: {e}{RESET}")
        traceback.print_exc()
        failed += 1

def main():
    global passed, failed
    print(f"\n{BOLD}{'='*60}")
    print("     BIOSHIELD HARD TEST SUITE v3.0")
    print(f"     6-Layer Defense-in-Depth")
    print(f"{'='*60}{RESET}")

    config_path = os.path.join(os.path.dirname(__file__), '..', 'bioshield-config.yaml')
    pipeline = BioShieldPipeline(config_path)
    print(f"\nLoaded {len(pipeline.screeners)} screeners: {[s.name for s in pipeline.screeners]}")

    # === BASELINES ===
    gfp = ("ATGCGTAAAGGCGAAGAGCTGTTCACTGGTGTCGTCCCTATTCTGGTGGAACTGGATGGTGATGTCAACGGTCATAAGTTTTCCGTGCG"
           "TGGCGAGGGTGAAGGTGACGCAACTAATGGTAAACTGACGCTGAAGTTCATCTGTACTACTGGTAAACTGCCGGTTCCTTGGCCGACTC"
           "TGGTAACGACGCTGACTTATGGTGTTCAGTGCTTTGCTCGTTATCCGGACCATATGAAGCAGCATGACTTCTTCAAGTCCGCCATGCCG"
           "GAAGGCTATGTGCAGGAACGCACGATTTCCTTTAAGGATGACGGCACGTACAAAACGCGTGCGGAAGTGAAATTTGAAGGCGATACCCT"
           "GGTAAACCGCATTGAGCTGAAAGGCATTGACTTTAAAGAAGACGGCAATATCCTGGGCCATAAGCTGGAATACAATTTTAACAGCCACAA"
           "TGTTTACATCACCGCCGATAAACAAAAAAATGGCATTAAAGCGAATTTTAAAATTCGCCACAACGTGGAGGATGGCAGCGTGCAGCTGGC"
           "TGATCACTACCAGCAAAACACTCCAATCGGTGATGGTCCTGTTCTGCTGCCAGACAATCACTATCTGAGCACGCAAAGCGTTCTGTCTA"
           "AAGATCCGAACGAGAAACGCGATCATATGGTTCTGCTGGAGTTCGTAACCGCAGCGGGCATCACGCATGGTATGGATGAACTGTACAAA"
           "TAA")
    # NOTE: GFP is a lab-engineered, human-codon-optimized gene.
    # With 6 layers, BioShield correctly flags it as "engineered" — this is CORRECT.
    # A real screening facility would then do human review and approve it.
    run_test("Safe GFP Gene (engineered)", gfp, [Verdict.FLAG, Verdict.REJECT], pipeline)

    anthrax_mock = "ATGCATGCATGC" * 50 + "TATA" * 20
    run_test("Anthrax Threat", anthrax_mock, [Verdict.FLAG, Verdict.REJECT], pipeline)

    # === FIX #1: SLIDING WINDOW ===
    print(f"\n{CYAN}--- Fix #1: Sliding Window ---{RESET}")
    random.seed(42)
    safe_flank = "".join(random.choices(['A','T','C','G'], weights=[0.29,0.29,0.21,0.21], k=2500))
    trojan = safe_flank[:2400] + anthrax_mock[:200] + safe_flank[2400:]
    run_test("Trojan Horse: 200bp threat in 2700bp safe", trojan, [Verdict.FLAG, Verdict.REJECT], pipeline, "Fix #1")

    # === FIX #3: BIFURCATED PIPELINE ===
    print(f"\n{CYAN}--- Fix #3: Bifurcated Pipeline ---{RESET}")
    run_test("Short Safe (37bp)", "ATGCGTAAAGGCGAAGAGCTGTTCACTGGTGTCGTCC", [Verdict.PASS], pipeline, "Fix #3")
    run_test("Short Trigger: Anthrax PA (18bp)", "ATGAAAAAACGGAGTTAT", [Verdict.FLAG, Verdict.REJECT], pipeline, "Fix #3")

    # === FIX #4: REVERSE COMPLEMENT ===
    print(f"\n{CYAN}--- Fix #4: Canonical K-mers ---{RESET}")
    run_test("RC of Anthrax (caught)", reverse_complement(anthrax_mock), [Verdict.FLAG, Verdict.REJECT], pipeline, "Fix #4")

    # === LAYER 4: CODON BIAS ===
    print(f"\n{CYAN}--- Layer 4: Codon Bias ---{RESET}")
    # Human-optimized codons for a short protein (all use top human-preferred codons)
    human_optimized = "ATGGCCACCGAGCTGAAGCAGGCCTTCGACAACGGCAGCATCAACTTCAGCGTGGCCGAGAACCTGATCATGGAGGCCATGCCCATGGCCTTC" * 3
    run_test("Human Codon-Optimized Sequence", human_optimized, [Verdict.FLAG, Verdict.REJECT], pipeline, "Layer 4")

    # === LAYER 5: CLEAVAGE SITES ===
    print(f"\n{CYAN}--- Layer 5: Cleavage Sites ---{RESET}")
    # Embed a Furin RRAR cleavage site in a protein-coding frame
    # RRAR = CGT CGT GCT CGT in DNA (frame 0)
    furin_seq = "ATG" + "GCT" * 50 + "CGTCGTGCTCGT" + "GCT" * 50 + "TAA"
    run_test("Furin Cleavage Site (RRAR)", furin_seq, [Verdict.FLAG, Verdict.REJECT], pipeline, "Layer 5")

    # === LAYER 6: RNA FOLDING ===
    print(f"\n{CYAN}--- Layer 6: RNA Folding ---{RESET}")
    # High-palindrome sequence that forms many hairpins
    hairpin = ("GCGCAATTGCGC" * 20 + "ATATATAT" * 5) * 2
    run_test("High RNA Hairpin Density", hairpin, [Verdict.FLAG, Verdict.REJECT], pipeline, "Layer 6")

    # === EDGE CASES ===
    print(f"\n{CYAN}--- Edge Cases ---{RESET}")
    run_test("Empty Sequence", "", [Verdict.PASS], pipeline, "Edge")

    chimera = gfp[:200] + anthrax_mock[:200] + gfp[200:400]
    run_test("Chimeric Splice", chimera, [Verdict.FLAG, Verdict.REJECT], pipeline, "Edge")

    # === SUMMARY ===
    print(f"\n{BOLD}{'='*60}")
    total = passed + failed
    print(f"  RESULTS: {GREEN}{passed} PASSED{RESET}, {RED}{failed} FAILED{RESET} out of {total}")
    print(f"{'='*60}{RESET}\n")
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
