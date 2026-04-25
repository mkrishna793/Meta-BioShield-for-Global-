# BioShield — AI-Resistant DNA Screening Pipeline

> **Track 1: DNA Screening & Synthesis Controls** | AIxBio Hackathon 2026 (Apart Research × BlueDot Impact × Cambridge Biosecurity Hub)

BioShield is a production-grade, 5-layer DNA synthesis screening pipeline that catches **AI-generated**, **novel**, and **evasion-variant** pathogens that legacy systems like the IBBIS Common Mechanism miss entirely.

---

## The Problem

Current DNA screening infrastructure relies on **exact sequence alignment** (BLAST/HMM). AI biological design tools like **Evo2** (40B parameters) and **RFdiffusion** can generate codon-optimized pathogen variants that break these exact alignments, rendering traditional screening blind to the most dangerous threats.

## The Solution

BioShield introduces **3 AI-defense layers** on top of the existing IBBIS architecture:

```
┌────────────────────────────────────────────────────────────┐
│                   IBBIS v2.0 API Server                    │
│                                                            │
│  ┌──────────────────┐    ┌───────────────────────────────┐ │
│  │  Legacy IBBIS     │    │  BioShield AI Defense Module  │ │
│  │  (BLAST/HMM)      │    │                               │ │
│  │                    │    │  Layer 1: K-mer Fingerprint   │ │
│  │  Catches known     │    │  Layer 2: ML Ensemble (RF+XGB)│ │
│  │  exact matches     │    │  Layer 3: Protein Impact +    │ │
│  │                    │    │           ESM-2 Embeddings    │ │
│  └──────────────────┘    └───────────────────────────────┘ │
│                                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Master Verdict Engine                     │ │
│  │     Combines both systems → PASS / FLAG / REJECT       │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

---

## Key Security Innovations

### 1. Sliding Window Architecture (Fix #1)
**Problem:** A bad actor hides 150bp of deadly virus inside 10,000bp of harmless plant DNA. Global feature extraction averages the threat signal into noise.  
**Solution:** Every sequence is chopped into **overlapping 500bp windows**. Each window is screened independently. If **any single window** flags, the entire order is rejected.

### 2. ESM-2 Protein Language Model (Fix #2)
**Problem:** Layer 3 compares against known UniProt toxins. A de novo toxin designed by AlphaFold has no sequence match — but its 3D folded shape is still lethal.  
**Solution:** When Meta's ESM-2 is installed, the system generates **protein shape embeddings** and compares functional geometry, not just letters. Catches novel toxins by shape.

### 3. Bifurcated Pipeline for Micro-Sequences (Fix #3)
**Problem:** K-mer and ML features produce random noise on sequences shorter than 100bp. Bad actors exploit this by ordering a virus in 50 tiny pieces from 50 companies.  
**Solution:** Sequences <100bp bypass ML entirely and go through an **exhaustive micro-trigger motif database** — exact-match search against critical pathogen initiation signals.

### 4. Canonical K-mers / Reverse-Complement Defense (Fix #4)
**Problem:** DNA is double-stranded. If a database has `ATGC`, a bad actor orders the reverse complement `GCAT`. The ML model sees completely different features.  
**Solution:** All k-mers are reduced to their **canonical (lexicographically smaller) form**. GC/AT skews are averaged across both strands. ORFs are checked on both strands. The system is now fully strand-agnostic.

---

## ML Model Performance

Trained on **41,607 real NCBI sequences** (E. coli, Yeast, Ebola, Smallpox, SARS-CoV-2, Nipah, Marburg, Anthrax) with extreme AI-evasion augmentation (15% point mutations, fragment insertion, reverse-complement variants):

| Model | ROC-AUC | Training Data |
|-------|---------|---------------|
| XGBoost (500 trees, GPU) | **0.983** | 41,607 sequences |
| Random Forest (300 trees) | **0.983** | 41,607 sequences |

**Accuracy: 97%** on held-out test set with AI-evasion and reverse-complement variants.

---

## Test Results (v2.0 — All 4 Fixes)

```
============================================================
     BIOSHIELD HARD TEST SUITE v2.0
     Testing ALL 4 Vulnerability Fixes
============================================================

[TEST] Safe GFP Gene (Baseline)              → OK FLAG  (ML prob=0.03)
[TEST] Anthrax Threat (Baseline)             → OK REJECT (ML prob=0.93)

[Fix #1] Trojan Horse: 200bp in 5000bp Safe  → OK REJECT (Sliding Window caught it)
[Fix #3] Short Safe Sequence (37bp)          → OK PASS  (MicroSequenceScreener)
[Fix #3] Short Trigger: Anthrax PA (18bp)    → OK FLAG  (Split-order attack detected)
[Fix #3] Short Random Junk (50bp)            → OK PASS
[Fix #4] Reverse-Complement of GFP           → OK FLAG  (ML prob=0.02, safe)
[Fix #4] Reverse-Complement of Anthrax       → OK REJECT (ML prob=0.93, caught)
[Edge]   Empty Sequence                      → OK PASS
[Edge]   Extreme GC (100%)                   → OK FLAG
[Edge]   Chimeric Splice (GFP+Anthrax+GFP)   → OK REJECT (ML prob=0.93)

RESULTS: 11 PASSED, 0 FAILED out of 11
============================================================
```

---

## IBBIS v2.0 Integration Demo

```
[SCENARIO 1] Standard Known Pathogen (Anthrax)
  Legacy IBBIS Engine: REJECT (Exact BLAST match)
  BioShield AI Defense: REJECT (K-mer + ML + Protein all FLAG)
  Final Action: REJECT ✓

[SCENARIO 2] AI Codon-Shuffled Evasion Variant (20% mutation)
  Legacy IBBIS Engine: PASS  ← MISSED IT (no exact alignment)
  BioShield AI Defense: REJECT (ML prob=0.96, K-mer 0.97 match)
  Final Action: REJECT ✓ ← BioShield saved the day
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/mkrishna793/Meta-BioShield-for-Global-.git
cd Meta-BioShield-for-Global-

# Install dependencies
pip install -r requirements.txt

# Set Python path
# Windows:
set PYTHONPATH=%cd%
# Linux/Mac:
export PYTHONPATH=$(pwd)

# Run IBBIS v2.0 demo
python demo_ibbis_v2.py

# Run full test suite
python tests/test_hard.py
```

---

## Project Structure

```
BioShield/
├── bioshield/
│   ├── pipeline.py              # Orchestrator (Sliding Window + Bifurcated routing)
│   ├── ibbis_integration.py     # IBBIS v2.0 Cloud API Connector
│   ├── verdict.py               # Risk aggregation engine
│   ├── config.py                # YAML configuration loader
│   ├── screeners/
│   │   ├── kmer_screener.py     # Layer 1: K-mer fingerprinting
│   │   ├── ml_screener.py       # Layer 2: RF + XGBoost ensemble
│   │   └── protein_impact.py    # Layer 3: 6-frame translation + ESM-2
│   ├── ml/
│   │   ├── features.py          # Canonical k-mer feature extraction
│   │   ├── train.py             # Local training script
│   │   └── models/              # Trained .joblib model files
│   ├── utils/
│   │   └── sequence.py          # Reverse complement, canonical k-mers
│   └── data/
│       ├── threat_kmers.json    # K-mer threat database
│       └── uniprot_toxins.json  # Curated toxin protein database
├── demo_ibbis_v2.py             # IBBIS v2.0 presentation demo
├── demo.py                      # Standalone BioShield demo
├── tests/
│   └── test_hard.py             # 11-scenario hard test suite (v2.0)
├── common-mechanism/            # IBBIS reference codebase
├── requirements.txt
└── README.md
```

---

## Technologies

- **Python 3.12+** — Pure Python, runs on Windows/Linux/Mac
- **scikit-learn 1.6+** — Random Forest classifier
- **XGBoost 2.0+** — Gradient-boosted tree ensemble (GPU-trained)
- **Biopython 1.87** — NCBI data fetching, 6-frame translation
- **ESM-2** (optional) — Meta's protein language model for de novo toxin detection
- **NumPy, zlib** — Canonical k-mer computation, Lempel-Ziv complexity

---

## License

MIT — Built for the AIxBio Hackathon 2026.

## Team

mkrishna793
