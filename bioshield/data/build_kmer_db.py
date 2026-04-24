import json
import os
import sys

# Add parent directory to path so we can import bioshield
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from bioshield.utils.sequence import kmer_frequency_vector
from itertools import product

def build_vocabs():
    vocabs = {}
    bases = ['A', 'C', 'G', 'T']
    for k in [4, 5, 6]:
        vocabs[str(k)] = [''.join(p) for p in product(bases, repeat=k)]
    return vocabs

def build_mock_db():
    """Build a mock threat database for the hackathon."""
    # In a real scenario, these would be pulled from NCBI (e.g. Anthrax, Ebola sequences)
    # Here we use synthetic signatures to demonstrate functionality.
    
    # Let's create a synthetic "ThreatX" sequence that is AT-rich and has a specific pattern
    threat_seq_1 = "ATGCATGCATGC" * 50 + "TATA" * 20  # Synthetic Bacillus anthracis mock
    threat_seq_2 = "CGCGCGCG" * 50 + "GATC" * 20      # Synthetic Variola virus mock
    
    organisms = {
        "Bacillus anthracis (Mock)": threat_seq_1,
        "Variola virus (Mock)": threat_seq_2
    }
    
    vocabs = build_vocabs()
    db = {}
    
    for org, seq in organisms.items():
        db[org] = {}
        for k in [4, 5, 6]:
            k_str = str(k)
            vec = kmer_frequency_vector(seq, k, vocab=vocabs[k_str])
            # Convert back to dict for JSON serialization, storing only non-zero to save space
            profile = {vocabs[k_str][i]: float(vec[i]) for i in range(len(vec)) if vec[i] > 0}
            db[org][k_str] = profile
            
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "threat_kmers.json")
    
    with open(out_path, 'w') as f:
        json.dump(db, f, indent=2)
        
    print(f"Built mock k-mer database at {out_path} with {len(db)} organisms.")

if __name__ == "__main__":
    build_mock_db()
