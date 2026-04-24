import os
import subprocess

def setup_test_files():
    """Create test FASTA files for the demo."""
    test_dir = "tests/fixtures"
    os.makedirs(test_dir, exist_ok=True)
    
    # Safe sequence: GFP
    gfp = ">safe_gfp\nATGCGTAAAGGCGAAGAGCTGTTCACTGGTGTCGTCCCTATTCTGGTGGAACTGGATGGTGATGTCAACGGTCATAAGTTTTCCGTGCGTGGCGAGGGTGAAGGTGACGCAACTAATGGTAAACTGACGCTGAAGTTCATCTGTACTACTGGTAAACTGCCGGTTCCTTGGCCGACTCTGGTAACGACGCTGACTTATGGTGTTCAGTGCTTTGCTCGTTATCCGGACCATATGAAGCAGCATGACTTCTTCAAGTCCGCCATGCCGGAAGGCTATGTGCAGGAACGCACGATTTCCTTTAAGGATGACGGCACGTACAAAACGCGTGCGGAAGTGAAATTTGAAGGCGATACCCTGGTAAACCGCATTGAGCTGAAAGGCATTGACTTTAAAGAAGACGGCAATATCCTGGGCCATAAGCTGGAATACAATTTTAACAGCCACAATGTTTACATCACCGCCGATAAACAAAAAAATGGCATTAAAGCGAATTTTAAAATTCGCCACAACGTGGAGGATGGCAGCGTGCAGCTGGCTGATCACTACCAGCAAAACACTCCAATCGGTGATGGTCCTGTTCTGCTGCCAGACAATCACTATCTGAGCACGCAAAGCGTTCTGTCTAAAGATCCGAACGAGAAACGCGATCATATGGTTCTGCTGGAGTTCGTAACCGCAGCGGGCATCACGCATGGTATGGATGAACTGTACAAATAA\n"
    with open(os.path.join(test_dir, "safe_gfp.fasta"), "w") as f:
        f.write(gfp)
        
    # Known Threat: Anthrax PA mock
    anthrax = ">threat_anthrax\n" + "ATGCATGCATGC" * 50 + "TATA" * 20 + "\n"
    with open(os.path.join(test_dir, "known_threat.fasta"), "w") as f:
        f.write(anthrax)
        
    # AI Evasion: Broken ORF + high repeat (mimics some evasion techniques)
    evasion = ">threat_ai_evasion_variant\n" + "CCCGGGAAATTT" * 40 + "\n"
    with open(os.path.join(test_dir, "evasion_variant.fasta"), "w") as f:
        f.write(evasion)
        
    # Protein Impact: Variola virus mock
    protein_threat = ">threat_variola\n" + "CGCGCGCG" * 50 + "GATC" * 20 + "\n"
    with open(os.path.join(test_dir, "protein_threat.fasta"), "w") as f:
        f.write(protein_threat)

    print(f"Created test fixtures in {test_dir}/")

def run_demo():
    print("==================================================")
    print("         BIOSHIELD 5-LAYER SCREENING DEMO         ")
    print("==================================================\n")
    
    setup_test_files()
    
    print("\n[Scenario 1] Screening known safe sequence (GFP)...")
    subprocess.run(["python", "-m", "bioshield.cli", "screen", "tests/fixtures/safe_gfp.fasta"])
    
    print("\n[Scenario 2] Screening known threat (Anthrax PA mock)...")
    subprocess.run(["python", "-m", "bioshield.cli", "screen", "tests/fixtures/known_threat.fasta"])
    
    print("\n[Scenario 3] Screening AI-shuffled evasion variant...")
    subprocess.run(["python", "-m", "bioshield.cli", "screen", "tests/fixtures/evasion_variant.fasta"])

if __name__ == "__main__":
    run_demo()
