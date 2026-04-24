# BioShield: Multi-Layered DNA Synthesis Screening Pipeline

> **A defense-in-depth system for detecting AI-designed pathogens and novel biological threats.**
> Built for the [AIxBio Hackathon 2026](https://apartresearch.com/sprints/aixbio-hackathon-2026-04-24-to-2026-04-26) — Track 1: DNA Screening & Synthesis Controls

---

## The Problem

Current DNA screening tools (BLAST, HMM) rely on **sequence similarity search**. If an AI tool like Evo2 redesigns a pathogen with different codons — producing the exact same deadly protein but with completely different DNA letters — these tools miss it entirely.

BioShield closes this gap with a **3-layer AI-resistant screening architecture** built on top of the [IBBIS Common Mechanism](https://github.com/ibbis-bio/common-mechanism).

## Architecture

```
Input FASTA ──> [ Layer 1: K-mer Fingerprinting     ]
                [ Layer 2: ML Ensemble Classifier    ] ──> Verdict Engine ──> PASS / FLAG / REJECT
                [ Layer 3: Protein Impact Analyzer   ]         |
                                                          Audit Trail
                                                     (Human-readable report)
```

### Layer 1: K-mer Fingerprinting (`kmer_screener.py`)
Extracts k-mer (k=4,5,6) frequency distributions and compares them against a database of known pathogen signatures using **cosine similarity**. Even when codons are scrambled by AI, the k-mer frequency distribution retains organism-specific signatures.

### Layer 2: ML Ensemble Classifier (`ml_screener.py`)
A **Random Forest + XGBoost** ensemble trained on 30,000+ real genomic sequences from NCBI (E. coli, Yeast, Ebola, Smallpox, SARS-CoV-2, Nipah, Marburg, Anthrax). Uses advanced biological features:

| Feature | Why It Matters |
|---|---|
| GC Content & Skews | Organism-specific nucleotide composition |
| CpG Dinucleotide Ratio | Viruses suppress CG pairs; AI models often forget this |
| Zlib Compression Complexity | Measures biological structure; AI DNA is often too "perfect" |
| K-mer Shannon Entropy | Information density of the sequence |
| Longest ORF Ratio | Pathogen genes tend to have long uninterrupted reading frames |
| Repeat Density | Engineered DNA often has abnormal tandem repeat patterns |

**ROC-AUC: 0.986** on a dataset with extreme AI-evasion mutations (point mutations, fragment insertion, codon shuffling).

### Layer 3: Protein Impact Analyzer (`protein_impact.py`)
Translates DNA in all 6 reading frames, finds ORFs, and aligns them against a curated UniProt toxin/virulence factor database. Answers **"What does this protein DO?"** — not just "Where did it come from?"

### Verdict Engine
- **PASS**: All layers clear
- **FLAG**: 1-2 layers flagged — human review required
- **REJECT**: 3+ layers flagged — automatic denial

Every verdict includes a full **audit trail** with per-layer explanations.

## Results

Hard test suite (8 scenarios):

| Test Case | K-mer | ML | Protein | Verdict |
|---|---|---|---|---|
| Safe GFP gene | PASS | PASS (0.01) | FLAG | FLAG |
| Anthrax threat signature | FLAG (1.00) | FLAG (0.76) | FLAG | **REJECT** |
| AI codon-shuffled variant | FLAG (0.98) | FLAG (0.83) | FLAG | **REJECT** |
| Short random junk (150bp) | PASS | PASS (0.10) | PASS | PASS |
| Long natural DNA (1500bp) | PASS | FLAG (0.88) | PASS | FLAG |
| Very short sequence (20bp) | FLAG | FLAG | PASS | FLAG |
| Extreme GC content (100%) | FLAG | PASS | FLAG | FLAG |
| Chimeric splice (safe+threat) | FLAG (0.96) | PASS (0.60) | FLAG | FLAG |

**Key result:** The AI codon-shuffled variant — designed to evade traditional BLAST — was caught and auto-rejected by all 3 layers.

## Quick Start

```bash
# Clone
git clone https://github.com/ibbis-bio/common-mechanism.git
cd BioShield

# Install
pip install -r requirements.txt

# Set Python path
# Windows:
set PYTHONPATH=D:\BioShield
# Linux/Mac:
export PYTHONPATH=$(pwd)

# Run demo
python demo.py

# Screen a specific FASTA file
python -m bioshield.cli screen path/to/sequence.fasta

# Output as JSON
python -m bioshield.cli screen path/to/sequence.fasta --json

# Run hard tests
python tests/test_hard.py
```

## Project Structure

```
BioShield/
├── bioshield/
│   ├── __init__.py
│   ├── cli.py                 # Command-line interface
│   ├── config.py              # YAML config loader
│   ├── pipeline.py            # Orchestrator: runs all screeners
│   ├── verdict.py             # Verdict engine (PASS/FLAG/REJECT)
│   ├── screeners/
│   │   ├── base.py            # Abstract BaseScreener + VerdictEngine
│   │   ├── kmer_screener.py   # Layer 1: K-mer fingerprinting
│   │   ├── ml_screener.py     # Layer 2: ML ensemble classifier
│   │   └── protein_impact.py  # Layer 3: Protein function analysis
│   ├── ml/
│   │   ├── features.py        # Advanced biological feature extraction
│   │   ├── train.py           # Model training pipeline
│   │   └── models/            # Pre-trained .joblib model files
│   ├── data/
│   │   ├── threat_kmers.json  # Pathogen k-mer signature database
│   │   └── uniprot_toxins.json # Curated toxin/virulence protein DB
│   └── utils/
│       └── sequence.py        # DNA/protein utility functions
├── common-mechanism/          # IBBIS commec fork (untouched)
├── tests/
│   └── test_hard.py           # 8-scenario hard test suite
├── demo.py                    # Automated demo script
├── bioshield-config.yaml      # Default configuration
├── requirements.txt
└── README.md
```

## ML Training (Kaggle)

The models were trained on Kaggle T4 GPUs using real NCBI genomic data:

- **Safe baseline:** E. coli K-12, Yeast (9,741 chunks)
- **Threat horizon:** Ebola, Smallpox, SARS-CoV-2, Nipah, Marburg, Anthrax (10,622 chunks)
- **AI-evasion augmentation:** Extreme mutations (15% point mutation rate + fragment insertion)
- **Total training set:** 30,985 sequences

## Future Work

- **SecureDNA integration:** The `BaseScreener` plugin architecture makes this a drop-in addition
- **IBBIS commec integration:** Parse commec JSON output as an additional screening layer
- **Expanded threat databases:** More NCBI accessions, more UniProt toxin entries
- **Real AI-evasion training:** Use actual Evo2/ProteinMPNN outputs as training data

## License

MIT License. Built on top of the [IBBIS Common Mechanism](https://github.com/ibbis-bio/common-mechanism) (MIT License).
