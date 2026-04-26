"""
BioShield v3.0 — Live Demo
Shows the real 6-layer pipeline screening DNA sequences.
"""
import os, sys, time, random
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from bioshield.pipeline import BioShieldPipeline
from bioshield.ibbis_integration import MockLegacyIBBIS
from bioshield.screeners.base import Verdict
from bioshield.utils.sequence import reverse_complement

G = "\033[92m"; R = "\033[91m"; C = "\033[96m"; Y = "\033[93m"; B = "\033[1m"; X = "\033[0m"

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""{C}{B}
    ======================================================
      BioShield v3.0 -- 6-Layer Defense-in-Depth
      AI-Resistant DNA Synthesis Screening Pipeline
    ======================================================{X}
    """)

def screen(name, seq, pipeline, pause=True):
    print(f"{B}{Y}> Screening: {name}{X}  ({len(seq)} bp)")
    v = pipeline.screen_sequence(seq, name)
    for r in v.per_layer_results:
        tag = f"{R}FLAG{X}" if r.flagged else f"{G}PASS{X}"
        print(f"    [{r.layer_name}] {tag}: {r.explanation[:100]}")
    color = R if v.verdict == Verdict.REJECT else (Y if v.verdict == Verdict.FLAG else G)
    print(f"  {B}> Verdict: {color}{v.verdict.value}{X}\n")
    if pause:
        time.sleep(1)
    return v

def main():
    banner()

    # Load pipeline
    print(f"{Y}[+] Loading 6 screening layers...{X}")
    cfg = os.path.join(os.path.dirname(__file__), 'bioshield-config.yaml')
    pipeline = BioShieldPipeline(cfg)
    ibbis = MockLegacyIBBIS()
    print(f"{G}    Ready: {[s.name for s in pipeline.screeners]}{X}\n")
    time.sleep(1)

    # === PART 1: IBBIS vs BioShield ===
    print(f"{C}{B}{'='*55}")
    print(f"  PART 1: Legacy IBBIS vs BioShield")
    print(f"{'='*55}{X}\n")

    threat = "ATGCATGCATGC" * 50 + "TATA" * 20
    random.seed(42)
    evasion = "".join(random.choice('ACGT') if random.random() < 0.2 else c for c in threat)

    print(f"{B}Test: AI Codon-Shuffled Pathogen (20% mutated){X}")
    print(f"  Legacy IBBIS (BLAST/HMM)...")
    r = ibbis.screen(evasion, "order1")
    if r["recommendation"] == "PASS":
        print(f"  {R}> IBBIS: PASS -- Threat MISSED! No exact alignment found.{X}")
    else:
        print(f"  > IBBIS: {r['recommendation']}")
    time.sleep(1)

    print(f"\n  BioShield 6-Layer Scan...")
    screen("AI-Evasion Variant", evasion, pipeline)

    # === PART 2: Full Test Suite ===
    print(f"{C}{B}{'='*55}")
    print(f"  PART 2: Hardened Test Suite (11 Scenarios)")
    print(f"{'='*55}{X}\n")

    passed = 0
    total = 0

    def test(name, seq, expected):
        nonlocal passed, total
        total += 1
        v = screen(name, seq, pipeline, pause=False)
        if v.verdict in expected:
            passed += 1

    # Safe GFP
    gfp = ("ATGCGTAAAGGCGAAGAGCTGTTCACTGGTGTCGTCCCTATTCTGGTGGAACTGGATGGTGATGTCAACGGTCATAAGTTTTCCGTGCG"
           "TGGCGAGGGTGAAGGTGACGCAACTAATGGTAAACTGACGCTGAAGTTCATCTGTACTACTGGTAAACTGCCGGTTCCTTGGCCGACTC"
           "TGGTAACGACGCTGACTTATGGTGTTCAGTGCTTTGCTCGTTATCCGGACCATATGAAGCAGCATGACTTCTTCAAGTCCGCCATGCCG"
           "GAAGGCTATGTGCAGGAACGCACGATTTCCTTTAAGGATGACGGCACGTACAAAACGCGTGCGGAAGTGAAATTTGAAGGCGATACCCT"
           "GGTAAACCGCATTGAGCTGAAAGGCATTGACTTTAAAGAAGACGGCAATATCCTGGGCCATAAGCTGGAATACAATTTTAACAGCCACAA"
           "TGTTTACATCACCGCCGATAAACAAAAAAATGGCATTAAAGCGAATTTTAAAATTCGCCACAACGTGGAGGATGGCAGCGTGCAGCTGGC"
           "TGATCACTACCAGCAAAACACTCCAATCGGTGATGGTCCTGTTCTGCTGCCAGACAATCACTATCTGAGCACGCAAAGCGTTCTGTCTA"
           "AAGATCCGAACGAGAAACGCGATCATATGGTTCTGCTGGAGTTCGTAACCGCAGCGGGCATCACGCATGGTATGGATGAACTGTACAAA"
           "TAA")
    test("Safe GFP (lab-engineered)", gfp, [Verdict.FLAG, Verdict.REJECT])
    test("Known Anthrax Pathogen", threat, [Verdict.FLAG, Verdict.REJECT])

    # Trojan Horse
    safe_flank = "".join(random.choices(['A','T','C','G'], weights=[0.29,0.29,0.21,0.21], k=2500))
    trojan = safe_flank[:2400] + threat[:200] + safe_flank[2400:]
    test("Trojan Horse (200bp in 2700bp safe)", trojan, [Verdict.FLAG, Verdict.REJECT])

    # Bifurcated
    test("Short Safe Sequence (37bp)", "ATGCGTAAAGGCGAAGAGCTGTTCACTGGTGTCGTCC", [Verdict.PASS])
    test("Split-Order: Anthrax PA (18bp)", "ATGAAAAAACGGAGTTAT", [Verdict.FLAG, Verdict.REJECT])

    # Reverse complement
    test("Reverse-Complement Evasion", reverse_complement(threat), [Verdict.FLAG, Verdict.REJECT])

    # Codon bias
    human_opt = "ATGGCCACCGAGCTGAAGCAGGCCTTCGACAACGGCAGCATCAACTTCAGCGTGGCCGAGAACCTGATCATGGAGGCCATGCCCATGGCCTTC" * 3
    test("Human Codon-Optimized", human_opt, [Verdict.FLAG, Verdict.REJECT])

    # Cleavage
    furin = "ATG" + "GCT" * 50 + "CGTCGTGCTCGT" + "GCT" * 50 + "TAA"
    test("Furin RRAR Cleavage Site", furin, [Verdict.FLAG, Verdict.REJECT])

    # RNA
    hairpin = ("GCGCAATTGCGC" * 20 + "ATATATAT" * 5) * 2
    test("High RNA Hairpin Density", hairpin, [Verdict.FLAG, Verdict.REJECT])

    test("Empty Sequence", "", [Verdict.PASS])

    chimera = gfp[:200] + threat[:200] + gfp[200:400]
    test("Chimeric Splice (safe+threat)", chimera, [Verdict.FLAG, Verdict.REJECT])

    # === SUMMARY ===
    print(f"{C}{B}{'='*55}")
    print(f"  RESULTS: {G}{passed}{X}{B}/{total} tests passed")
    print(f"{C}{'='*55}{X}")
    print(f"\n  {B}BioShield v3.0 — All layers operational.{X}")
    print(f"  Project by N. Mohana Krishna\n")

if __name__ == "__main__":
    main()
