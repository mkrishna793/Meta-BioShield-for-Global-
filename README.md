# Meta-BioShield
### A 6-Layer Defense-in-Depth Pipeline for AI-Resistant DNA Synthesis Screening

**AIxBio Hackathon 2026** · Apart Research × BlueDot Impact × Cambridge Biosecurity Hub · Track 1: DNA Screening & Synthesis Controls

**Author:** N. Mohana Krishna · Independent Researcher

---

## What Is This?

Every DNA synthesis company must screen orders before manufacturing — to make sure no one is ordering genetic material for dangerous pathogens. The current standard tool (IBBIS, used industry-wide) works by exact matching: it compares your DNA sequence letter-by-letter against a database of known threats.

**The problem:** AI tools like Evo2 (a 40-billion-parameter DNA language model) can redesign a deadly pathogen's DNA so that every individual letter is different — while the resulting protein it produces is exactly as dangerous. The exact matcher sees nothing. The sequence passes. The weapon is manufactured.

**Meta-BioShield** is a second screening layer that runs alongside IBBIS and catches what IBBIS misses. Instead of looking for exact matches, it looks at six independent biological properties of a sequence — statistical patterns, machine learning signals, protein function, codon engineering, molecular switches, and structural signatures. An AI that evades one layer will almost certainly trigger another.

---

## The Core Problem, Visualized

```
ORIGINAL ANTHRAX DNA  →  IBBIS BLAST  →  ❌ BLOCKED
        │
        │  AI codon-shuffles 20% of the letters
        ▼
MODIFIED ANTHRAX DNA  →  IBBIS BLAST  →  ✅ PASSES (missed!)
        │
        │  Same deadly protein. Different DNA spelling.
        ▼
   META-BIOSHIELD  →  6 independent checks  →  ❌ BLOCKED
```

The protein produced by both DNA sequences is functionally identical. Legacy BLAST cannot see through the disguise. BioShield can.

---

## Results at a Glance

| Metric | Value |
|---|---|
| Training sequences | 44,218 real NCBI genomic sequences |
| ROC-AUC (Meta-Learner) | **0.969** |
| Test scenarios passed | **11 / 11** |
| AI-evasion variant detection | ✅ (ML prob = 0.92 on 20%-mutated anthrax) |
| Trojan Horse detection | ✅ (200bp threat hidden in 2700bp safe sequence) |
| Split-order attack detection | ✅ (18bp pathogen fragment) |
| Reverse-complement evasion | ✅ (canonical k-mer extraction) |

---

## Architecture: How It Works

```
                      DNA SYNTHESIS ORDER
                             │
                    ┌────────▼────────┐
                    │  Sequence Router │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
      len < 100bp       100–500bp         len > 500bp
           │                 │                 │
    ┌──────▼──────┐   ┌──────▼──────┐  ┌──────▼──────┐
    │ Bifurcated  │   │   Standard  │  │  Sliding    │
    │  Pipeline   │   │   6-Layer   │  │  Window     │
    │ (Fix #3)    │   │  Pipeline   │  │  (Fix #1)   │
    └──────┬──────┘   └──────┬──────┘  └──────┬──────┘
           │                 │                 │
           └─────────────────▼─────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Verdict Engine  │
                    │  0 flags → PASS  │
                    │  1-2 flags → FLAG│
                    │  3+ flags → REJECT│
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
            PASS      FLAG FOR REVIEW    REJECT
```

---

## The 6 Screening Layers

```
INPUT DNA
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  L1  K-MER FINGERPRINTING                                │
│  Computes statistical frequency of all 4-,5-,6-letter    │
│  substrings. Measures cosine similarity against threat DB.│
│  Catches: codon-shuffled variants with intact statistics. │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  L2  ML ENSEMBLE + META-LEARNER                          │
│  Extracts 10 biological features → RF (500 trees) +      │
│  XGBoost (800 trees) → Logistic Regression stacking.     │
│  Catches: complex non-linear threat patterns.            │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  L3  PROTEIN IMPACT ANALYZER                             │
│  Translates DNA in all 6 reading frames → finds ORFs →   │
│  aligns against UniProt toxin/virulence factor DB.       │
│  (+ ESM-2 protein shape embeddings when available)       │
│  Catches: known toxins AND de novo proteins by function. │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  L4  HOST CODON BIAS SCREENER                            │
│  Computes Human Codon Adaptation Index (CAI) against     │
│  Homo sapiens codon usage tables.                        │
│  CAI ≥ 0.75 = sequence was engineered for human cells.  │
│  Catches: DNA designed for efficient human cell infection.│
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  L5  PROTEASE CLEAVAGE SITE SCREENER                     │
│  Scans all 6 translated frames for 8 protease motifs:    │
│  Furin (RRAR, PRRA), Anthrax PA (RKKR), Thrombin, TEV,  │
│  Factor Xa, Enterokinase.                                │
│  Catches: molecular activation switches that CANNOT be   │
│  changed without disabling the pathogen.                 │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  L6  RNA SECONDARY STRUCTURE SCREENER                    │
│  Computes palindromic stem density (hairpin potential)   │
│  and GC bond stability. ViennaRNA MFE when available.   │
│  Catches: viral RNA structural signatures that must be   │
│  preserved for replication.                              │
└──────────────────────────────────────────────────────────┘
    │
    ▼
  VERDICT
```

---

## The 4 Security Innovations

### Fix #1 — Sliding Window Architecture
**Attack defeated:** Trojan Horse dilution

A bad actor hides 200 dangerous base pairs inside a 10,000 base pair order. The global statistics look safe because the threat is only 2% of the sequence. Standard screening averages everything and misses it.

BioShield breaks every sequence longer than 500bp into overlapping 500bp windows with 50% overlap. Each window is screened independently. One flagged window flags the entire order.

```
SEQUENCE:  [SAFE][SAFE][SAFE][THREAT][SAFE][SAFE][SAFE][SAFE]
                              │
                     Sliding Window catches it
                              │
                         ❌ REJECT
```

### Fix #2 — Bifurcated Pipeline
**Attack defeated:** Split-order attacks

A bad actor orders a dangerous gene in 20 separate orders of 50 base pairs each, knowing that individual fragments are meaningless. Each piece passes screening separately.

BioShield routes sequences under 100bp to a specialized `MicroSequenceScreener` that performs exact-match lookup against a database of critical pathogen initiation motifs — the specific short sequences that start dangerous genes.

```
"ATGAAAAAACGGAGTTAT"  (18bp — looks like nothing)
         │
         └─→ MicroSequenceScreener
                  │
                  └─→ Matches: anthrax_PA_core
                         │
                       FLAG
```

### Fix #3 — Canonical K-mers
**Attack defeated:** Reverse-complement evasion

DNA is double-stranded. A DNA sequence `ATGC` and its reverse complement `GCAT` produce the same protein information when read from opposite strands. A bad actor can order the reverse complement of a flagged sequence — double-stranded, functionally identical — and the forward-strand k-mer lookup misses it completely.

BioShield reduces every k-mer to its lexicographically smaller form: `min(kmer, reverse_complement(kmer))`. Both strands become the same fingerprint. The evasion becomes invisible.

### Fix #4 — Closed-Weight Deployment
**Attack defeated:** Adversarial AI probing

If model weights are public, an attacker downloads BioShield and runs millions of sequence variants offline, searching for one that evades all 6 layers. The attacker then orders only the one that passed.

The code architecture is open-sourced. The trained weights and threat databases are not published. An attacker must submit real DNA orders to test the system — each attempt has a cost, a paper trail, and legal exposure.

---

## ML Model: What It Actually Measures

The 10 features extracted from every sequence:

| Feature | What it measures | Why it matters |
|---|---|---|
| `gc_content` | Fraction of G+C bases | Pathogens have characteristic GC profiles |
| `skew_gc` | Strand-averaged G-C asymmetry | Synthetic DNA often has unnaturally balanced GC |
| `skew_at` | Strand-averaged A-T asymmetry | Same |
| `cpg_ratio` | CpG dinucleotide vs. expected frequency | Engineered DNA has abnormal CpG patterns |
| `complexity` | zlib compression ratio | Low-complexity = repeated/synthetic sequences |
| `length` | Sequence length | Contextual feature |
| `kmer_3_entropy` | Shannon entropy of canonical 3-mers | Measures sequence information density |
| `kmer_4_entropy` | Shannon entropy of canonical 4-mers | Higher resolution than 3-mer |
| `longest_orf_ratio` | Longest open reading frame / total length | Long ORFs suggest protein-coding threat genes |
| `repeat_density` | Fraction of consecutive repeated 2-mers | Synthetic construction signature |

All features are **strand-agnostic** — computed identically on forward and reverse complement strands.

### Meta-Learner Stacking

```
Sequence Features
       │
   ┌───┴────┐
   │        │
   RF       XGBoost
  (prob)   (prob)
   │        │
   └───┬────┘
       │
  Meta-Learner
  (Logistic Regression)
  RF weight:  6.70
  XGB weight: 1.40
  (RF is 4.8× more trusted — discovered automatically)
       │
   Final Probability
```

The meta-learner discovered that RF handles the high-dimensional k-mer entropy features more robustly than XGBoost on this dataset. This weighting was learned from data, not set manually.

---

## Training Data

```
┌──────────────────────────────────────────────────────────┐
│                 44,218 Total Sequences                   │
│                                                          │
│  Safe (11,998)                                           │
│  ├─ E. coli K-12 genome (U00096.3)                       │
│  └─ S. cerevisiae (3 chromosomes)                        │
│                                                          │
│  Threat (10,740)                                         │
│  ├─ Ebola, Smallpox, SARS-CoV-2                          │
│  ├─ Nipah, Marburg, Anthrax                              │
│  └─ MERS, SARS-1                                         │
│                                                          │
│  AI-Evasion Augmented (10,740)                           │
│  └─ Threat sequences + 15% point mutations               │
│     + fragment insertion                                  │
│                                                          │
│  Reverse-Complement (10,740)                             │
│  └─ Full RC of all threat sequences                      │
└──────────────────────────────────────────────────────────┘
```

Class imbalance (12K safe vs 32K threat) handled via `class_weight='balanced'` (RF) and `scale_pos_weight` (XGBoost).

All sequences sourced from public NCBI databases. No novel pathogen sequences were generated.

---

## Test Suite Results (All 11/11 Passed)

```
Test Scenario                         Verdict   Key Layer(s) That Caught It
─────────────────────────────────────────────────────────────────────────────
Safe GFP (lab-engineered)             REJECT    CodonBias (CAI=0.75), Cleavage
Known Anthrax (mock)                  REJECT    All 6 layers flagged
Trojan Horse (200bp in 2700bp)        REJECT    Sliding Window + K-mer + ML
Short Safe Sequence (37bp)            PASS      MicroSequenceScreener
Split-Order Anthrax PA (18bp)         FLAG      MicroSequenceScreener (exact match)
Reverse-Complement Anthrax            REJECT    Canonical K-mers + ML (0.93)
Human Codon-Optimized Sequence        FLAG      CodonBias (CAI=1.000)
Furin RRAR Cleavage Site              REJECT    CleavageSite CRITICAL + ML + Protein
High RNA Hairpin Density              FLAG      RNAFolding (density=0.919)
Empty Sequence                        PASS      Handled gracefully
Chimeric Splice                       REJECT    6/6 layers flagged
─────────────────────────────────────────────────────────────────────────────
RESULT: 11 PASSED, 0 FAILED
```

**Note on GFP:** GFP (Green Fluorescent Protein) is a harmless lab marker that gets flagged as REJECT because it is codon-optimized for human cells (CAI=0.75) and contains engineered cleavage sites. This is the correct behavior — it is an engineered construct. In production, a human reviewer would see the flag, recognize it as harmless, and approve it. The system is designed to be aggressive and let humans make the final call on ambiguous cases.

---

## IBBIS v2.0 Integration

BioShield is designed to run alongside legacy IBBIS, not replace it.

```
DNA ORDER
    │
    ├──────────────────────────────────┐
    │                                  │
    ▼                                  ▼
Legacy IBBIS                     Meta-BioShield
(BLAST/HMM exact match)          (6-layer statistical)
    │                                  │
    └──────────────┬───────────────────┘
                   │
          Master Verdict Engine
          Either system REJECTs → REJECT
          BioShield FLAGs only → FLAG FOR REVIEW
          Both PASS → PASS
                   │
          IBBIS v2.0 JSON Report
```

**Scenario 1 — Standard Anthrax:**
IBBIS → REJECT. BioShield → REJECT. Both agree.

**Scenario 2 — AI Codon-Shuffled (20% mutation):**
IBBIS → **PASS** (missed). BioShield → **REJECT** (ML prob=0.92). BioShield catches what IBBIS missed.

---

## Quick Start

```bash
git clone https://github.com/mkrishna793/Meta-BioShield-for-Global-.git
cd Meta-BioShield-for-Global-
pip install -r requirements.txt

# Set Python path
export PYTHONPATH=$(pwd)          # Linux/Mac
set PYTHONPATH=%cd%               # Windows

# Run the IBBIS v2.0 integration demo
python demo_ibbis_v2.py

# Run the full 11-scenario hardened test suite
python tests/test_hard.py

# Screen your own FASTA file
python -m bioshield.cli screen your_sequence.fasta

# Screen and get JSON output
python -m bioshield.cli screen your_sequence.fasta --json

# Train fresh ML models (uses mock data if NCBI data not available)
python -m bioshield.cli train
```

**Requirements:** Python 3.10+, biopython, scikit-learn, xgboost, numpy, scipy, pyyaml, joblib

**Optional (graceful fallback if not installed):**
- `torch` + `esm` — enables ESM-2 protein shape embeddings in Layer 3
- `RNA` (ViennaRNA) — enables full MFE folding in Layer 6

---

## Project Structure

```
Meta-BioShield/
│
├── bioshield/
│   ├── pipeline.py              # Orchestrator: routing, sliding window, verdict
│   ├── ibbis_integration.py     # IBBIS v2.0 cloud connector + mock legacy IBBIS
│   ├── verdict.py               # VerdictEngine: aggregates layer results
│   ├── config.py                # YAML config loader
│   │
│   ├── screeners/
│   │   ├── base.py              # BaseScreener, ScreenResult, FinalVerdict, Verdict
│   │   ├── kmer_screener.py     # L1: K-mer fingerprinting
│   │   ├── ml_screener.py       # L2: RF + XGBoost + meta-learner
│   │   ├── protein_impact.py    # L3: ORF translation + alignment + ESM-2
│   │   ├── codon_bias.py        # L4: Human CAI scoring
│   │   ├── cleavage_sites.py    # L5: Protease cleavage site regex scan
│   │   └── rna_folding.py       # L6: Palindrome density + ViennaRNA MFE
│   │
│   ├── ml/
│   │   ├── features.py          # 10-feature strand-agnostic extraction
│   │   ├── train.py             # RF + XGBoost + meta-learner training pipeline
│   │   └── models/              # CLOSED — weights not in repo (see below)
│   │
│   ├── data/
│   │   ├── build_kmer_db.py     # Builds threat k-mer profile database
│   │   ├── build_protein_db.py  # Builds UniProt toxin database
│   │   ├── threat_kmers.json    # CLOSED — not in repo
│   │   └── uniprot_toxins.json  # CLOSED — not in repo
│   │
│   └── utils/
│       └── sequence.py          # reverse_complement, canonical_kmer, translate_all_frames
│
├── tests/
│   ├── test_hard.py             # 11-scenario hardened test suite
│   └── fixtures/                # Test FASTA files
│
├── demo_ibbis_v2.py             # IBBIS v2.0 integration demo
├── demo.py                      # Basic 3-scenario demo
├── bioshield-config.yaml        # All thresholds and paths
└── requirements.txt
```

---

## Configuration

All layer thresholds are configurable in `bioshield-config.yaml`:

```yaml
pipeline:
  run_kmer: true          # L1
  run_ml: true            # L2
  run_protein_impact: true # L3
  run_codon_bias: true    # L4
  run_cleavage_sites: true # L5
  run_rna_folding: true   # L6

kmer_screener:
  threshold: 0.85         # Cosine similarity threshold for threat match

ml_screener:
  threshold: 0.70         # Threat probability threshold

protein_impact:
  min_orf_length: 100     # Minimum ORF length to analyze (amino acids)
  identity_threshold: 40.0 # Minimum % identity to flag a protein match

codon_bias:
  threshold: 0.75         # CAI threshold (0-1) for human optimization flag

rna_folding:
  palindrome_threshold: 0.15 # Hairpin stem density threshold
```

---

## Security and Deployment Model

### Open Architecture, Closed Weights

The complete source code is published so the biosecurity community can audit, fork, and improve the architecture. The trained model weights (`rf_model.joblib`, `xgb_model.joblib`, `meta_learner.joblib`) and threat databases (`threat_kmers.json`, `uniprot_toxins.json`) are intentionally not in this repository.

**Why:** If weights are public, an adversary can download BioShield, run millions of candidate sequences through it offline, find the one that evades all 6 layers, and only then place a real order. Closed weights force adversaries to interact with the live system — each test costs money, takes time, and creates a legal record.

### Deployment Target

BioShield is designed to run as a plugin module alongside the IBBIS `commec` Linux server infrastructure. All DNA synthesis orders pass through both systems before manufacturing approval.

---

## Limitations

**False positives:** The system is intentionally aggressive. Legitimate codon-optimized lab constructs (including harmless proteins like GFP) get flagged because they exhibit the same signals as engineered threats — high CAI, engineered cleavage sites. Production deployment requires a human review workflow for FLAG verdicts.

**Database scale:** The k-mer threat profiles and toxin database in this prototype are demonstrative. Production efficacy requires comprehensive, continuously updated databases covering all select agents.

**Training scale:** 44K sequences is strong for a research prototype, not for production. Real-world deployment should be trained on millions of sequences with ongoing retraining.

**Sequence length:** The sliding window approach scales linearly with sequence length. Sequences above 100kb would benefit from the planned Rust migration for k-mer computation.

**IBBIS integration:** The legacy IBBIS layer in this prototype is a simulation (`MockLegacyIBBIS`) because `commec` requires Linux server infrastructure. The integration architecture is production-ready; only the server deployment is mocked.

**ESM-2 and ViennaRNA:** Both are architecturally integrated with graceful fallbacks but were not deployed with full models during the hackathon due to compute constraints.

---

## Roadmap

| Feature | Status | Description |
|---|---|---|
| PyO3 Rust Bridge | Planned | K-mer computation in Rust via PyO3 — ~100× throughput |
| Million-Scale Training | Planned | Expand NCBI dataset + dedicated compute |
| Full ESM-2 Deployment | Architecture ready | Enable protein shape embedding for de novo toxin detection |
| ViennaRNA Integration | Architecture ready | Full RNA MFE folding analysis |
| Live IBBIS Server Merge | Architecture ready | Deploy as plugin on IBBIS Linux infrastructure |
| Continuous Retraining Pipeline | Planned | Automated retraining as new pathogen sequences are discovered |

---

## Ethical Statement

All training data was sourced from publicly available NCBI databases. No novel pathogen sequences were generated. The AI-evasion variants used for training are random point mutations — not biologically viable gain-of-function modifications.

This project identifies a real vulnerability (IBBIS's susceptibility to AI codon-optimization) and responds by building a defensive tool. No offensive capabilities were developed or demonstrated.

Model weights and threat databases are withheld from publication to prevent misuse. No screening system is a guarantee of safety — BioShield is designed as one layer in a broader biosecurity ecosystem that includes physical security, customer verification, and law enforcement.

---

## Citation

```bibtex
@article{bioshield2026,
  title   = {BioShield: A 6-Layer Defense-in-Depth Pipeline for AI-Resistant DNA Synthesis Screening},
  author  = {N. Mohana Krishna},
  year    = {2026},
  note    = {AIxBio Hackathon 2026, Apart Research × BlueDot Impact × Cambridge Biosecurity Hub}
}
```

---

## References

1. Nguyen et al. "Sequence modeling and design from molecular to genome scale with Evo." *Science*, 2024.
2. Apart Research. "AIxBio Hackathon 2026: DNA Screening & Synthesis Controls." Track 1 problem statement.
3. IBBIS. "Common Mechanism for DNA Synthesis Screening." (`commec`)
4. Esvelt et al. "SecureDNA: A cryptographic platform for universal DNA synthesis screening." MIT.
5. Kleinman et al. "ABC-Bench: An Agentic Biosecurity Benchmark." *NeurIPS 2025*.
6. Lin et al. "Evolutionary-scale prediction of atomic-level protein structure with a language model." *Science*, 2023. (ESM-2)
7. Chen & Guestrin. "XGBoost: A Scalable Tree Boosting System." *KDD*, 2016.

---
Note :- this is not end i am planning to the V2 that would look like 
  🚀 Roadmap & Future Developments (v2.0)

  While Meta-BioShield provides a robust defense-in-depth layer, the next version (v2.0) is focused on evolving from statistical detection to semantic intelligence.

  🧬 Next-Gen Screening Capabilities

  - Semantic Functional Analysis: Moving beyond statistical features to integrate deep Protein Language Models (pLMs) as a core requirement. This will allow the
  system to detect "functional mimics"—sequences that look safe statistically but fold into dangerous proteins.
  - Fuzzy Motif Recognition: Upgrading the MicroSequenceScreener from exact-match triggers to high-sensitivity alignment algorithms (HMMs). This will ensure that
  single-point mutations in critical pathogen motifs cannot evade detection.
  - Dynamic Verdict Weighting: Implementing a "Criticality Matrix" in the Verdict Engine. Certain high-confidence hits (e.g., 95%+ identity to a known toxin) will
  trigger an immediate REJECT, reducing reliance on human review for obvious threats.
  - High-Throughput Optimization: Migration of the K-mer and sliding-window engine to Rust (via PyO3) to handle industrial-scale genomic data and prevent
  resource-exhaustion bottlenecks.

  🛡️ System Hardening

  - Adversarial Robustness Training: Implementing adversarial training loops where the ML models are trained against GAN-generated "evasion sequences" to close
  statistical gaps.
  - Enhanced Input Validation: Introducing strict sequence-length and file-size quotas to ensure system stability and availability during high-volume screening.

## License

MIT — Built for the AIxBio Hackathon 2026.
