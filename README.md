# BioShield — 6-Layer AI-Resistant DNA Screening Pipeline

> **Track 1: DNA Screening & Synthesis Controls** | AIxBio Hackathon 2026 (Apart Research x BlueDot Impact x Cambridge Biosecurity Hub)

BioShield is a production-grade, **6-layer Defense-in-Depth** DNA synthesis screening pipeline that catches **AI-generated**, **novel**, and **evasion-variant** pathogens that legacy systems like the IBBIS Common Mechanism miss.

---

## The Problem

Current DNA screening relies on **exact sequence alignment** (BLAST/HMM). AI tools like **Evo2** (40B params) and **RFdiffusion** can generate codon-optimized variants that break these alignments. Legacy screening becomes blind.

## The Solution: 6-Layer Defense-in-Depth

```
┌─────────────────────────────────────────────────────────────┐
│                    IBBIS v2.0 API Server                    │
│                                                             │
│  ┌─────────────────┐   ┌──────────────────────────────────┐ │
│  │ Legacy IBBIS     │   │  BioShield AI Defense Module     │ │
│  │ (BLAST/HMM)      │   │                                  │ │
│  │                   │   │  L1: K-mer Fingerprinting        │ │
│  │ Catches known     │   │  L2: ML Ensemble + Meta-Learner  │ │
│  │ exact matches     │   │  L3: Protein Impact + ESM-2      │ │
│  │                   │   │  L4: Host Codon Bias (CAI)       │ │
│  │                   │   │  L5: Protease Cleavage Sites     │ │
│  │                   │   │  L6: RNA Secondary Structure     │ │
│  └─────────────────┘   └──────────────────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Master Verdict Engine                      │ │
│  │    Combines all layers → PASS / FLAG / REJECT           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## The 6 Layers

| Layer | What it checks | What it catches |
|-------|----------------|-----------------|
| **L1: K-mer Fingerprinting** | Statistical k-mer distribution (k=4,5,6) | Heavily mutated/codon-shuffled pathogen variants |
| **L2: ML Ensemble** | RF + XGBoost + Logistic Regression meta-learner | Complex non-linear threat patterns in GC, CpG, complexity |
| **L3: Protein Impact** | 6-frame ORF translation + alignment (+ ESM-2 embeddings) | Known toxins AND de novo toxins by functional shape |
| **L4: Codon Bias** | Human Codon Adaptation Index (CAI) | Sequences engineered for human cell expression |
| **L5: Cleavage Sites** | Furin, Thrombin, TEV, Factor Xa motif scanning | Unalterable "activation switches" that make toxins lethal |
| **L6: RNA Folding** | Palindrome density + hairpin analysis (ViennaRNA optional) | Viral RNA structural signatures |

## Security Innovations

| Innovation | Attack it defeats |
|------------|-------------------|
| **Sliding Window** (500bp, 50% overlap) | Trojan Horse: hiding 150bp threat in 10,000bp safe DNA |
| **Bifurcated Pipeline** (<100bp → micro-trigger search) | Split-order: ordering a virus in 50 tiny pieces |
| **Canonical K-mers** (strand-agnostic) | Reverse-complement: ordering the opposite DNA strand |
| **Black Box Deployment** (closed weights) | Adversarial AI: testing millions of evasion sequences offline |

---

## ML Model Performance

Trained on **41,607 real NCBI sequences** with extreme AI-evasion augmentation:

| Model | ROC-AUC | Accuracy |
|-------|---------|----------|
| XGBoost (500 trees, GPU) | **0.983** | 97% |
| Random Forest (300 trees) | **0.983** | 97% |

---

## Test Results (v3.0 — 6 Layers)

```
Loaded 6 screeners: [KmerScreener, MLScreener, ProteinImpactScreener,
                      CodonBiasScreener, CleavageSiteScreener, RNAFoldingScreener]

Safe GFP Gene (engineered)              → REJECT (correctly flags lab construct)
Anthrax Threat                          → REJECT (6/6 layers agree)
Trojan Horse: 200bp in 2700bp safe      → REJECT (Sliding Window caught it)
Short Safe (37bp)                       → PASS  (MicroSequenceScreener)
Short Trigger: Anthrax PA (18bp)        → FLAG  (split-order detected)
RC of Anthrax                           → REJECT (canonical k-mers caught it)
Human Codon-Optimized Sequence          → FLAG  (CAI = 1.000)
Furin Cleavage Site (RRAR)              → REJECT (CRITICAL activation switch)
High RNA Hairpin Density                → FLAG  (viral folding pattern)
Empty Sequence                          → PASS
Chimeric Splice                         → REJECT

RESULTS: 11 PASSED, 0 FAILED out of 11
```

---

## Security & Deployment Philosophy

> "BioShield assumes the biosecurity landscape is an adversarial arms race. We built it not as a static wall, but as a multi-layered Defense-in-Depth architecture. By enforcing biological constraints at 6 independent levels, we exponentially raise the computational cost for any adversary."

### Open Architecture, Closed Weights

The **code architecture** is open-sourced so the community can audit and improve it. The **trained model weights and threat databases** are NOT published. They are deployed as a closed Black Box API within trusted screening networks (like SecureDNA).

This prevents adversarial AI from testing millions of evasion sequences offline. If a bad actor wants to test BioShield, they must submit real DNA orders — triggering cost, speed, and legal traps.

---

## Future Development Roadmap

| Feature | Status | Description |
|---------|--------|-------------|
| **PyO3 Rust Bridge** | Planned | Move K-mer computation to Rust via PyO3 for 100x speed |
| **Million-Scale Training** | Planned | Train on millions of sequences (requires dedicated compute) |
| **ESM-2 Full Integration** | Architecture Ready | Enable Meta's protein language model for de novo toxin detection |
| **ViennaRNA Integration** | Architecture Ready | Enable full RNA MFE folding analysis |
| **Live IBBIS Server Merge** | Architecture Ready | Deploy as a plugin on IBBIS Linux infrastructure |

---

## Quick Start

```bash
git clone https://github.com/mkrishna793/Meta-BioShield-for-Global-.git
cd Meta-BioShield-for-Global-
pip install -r requirements.txt

# Windows:
set PYTHONPATH=%cd%
# Linux/Mac:
export PYTHONPATH=$(pwd)

# Run IBBIS v2.0 demo
python demo_ibbis_v2.py

# Run full 6-layer test suite
python tests/test_hard.py
```

> **Note:** Model weights are not included in this repository. See `bioshield/ml/models/WEIGHTS_CLOSED.md` for details.

---

## Project Structure

```
BioShield/
├── bioshield/
│   ├── pipeline.py              # 6-layer orchestrator + sliding window
│   ├── ibbis_integration.py     # IBBIS v2.0 Cloud API connector
│   ├── verdict.py               # Risk aggregation engine
│   ├── screeners/
│   │   ├── kmer_screener.py     # L1: K-mer fingerprinting
│   │   ├── ml_screener.py       # L2: ML ensemble + meta-learner
│   │   ├── protein_impact.py    # L3: Protein impact + ESM-2
│   │   ├── codon_bias.py        # L4: Host codon bias (CAI)
│   │   ├── cleavage_sites.py    # L5: Protease cleavage sites
│   │   └── rna_folding.py       # L6: RNA secondary structure
│   ├── ml/
│   │   ├── features.py          # Canonical k-mer feature extraction
│   │   └── models/              # CLOSED — not in repo
│   └── utils/
│       └── sequence.py          # Reverse complement, canonical k-mers
├── demo_ibbis_v2.py
├── tests/test_hard.py           # 11-scenario test suite (v3.0)
├── common-mechanism/            # IBBIS reference
└── requirements.txt
```

## License

MIT — Built for the AIxBio Hackathon 2026.

## Team

mkrishna793
