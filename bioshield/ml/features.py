import numpy as np
from collections import Counter
import math
from bioshield.utils.sequence import extract_kmers

def shannon_entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in counter.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy

def extract_features(seq: str) -> dict:
    """Extract machine learning features from a DNA sequence."""
    seq = seq.upper()
    length = len(seq)
    
    if length == 0:
        return {
            "gc_content": 0.0,
            "length": 0,
            "kmer_3_entropy": 0.0,
            "kmer_4_entropy": 0.0,
            "longest_orf_ratio": 0.0,
            "repeat_density": 0.0
        }
        
    import zlib
    
    # 1. GC Content & Skews
    a = seq.count('A')
    t = seq.count('T')
    g = seq.count('G')
    c = seq.count('C')
    gc_content = (g + c) / length
    
    skew_gc = (g - c) / max(1, (g + c))
    skew_at = (a - t) / max(1, (a + t))
    
    # 2. CpG Dinucleotide Ratio (Key for catching synthetic DNA)
    cg_count = seq.count('CG')
    expected_cg = (c * g) / max(1, length)
    cpg_ratio = cg_count / expected_cg if expected_cg > 0 else 0.0
    
    # 3. Sequence Complexity (zlib compression ratio)
    compressed_len = len(zlib.compress(seq.encode('utf-8')))
    complexity = compressed_len / max(1, length)
    
    # 4. K-mer Entropies
    k3_counts = extract_kmers(seq, 3)
    k4_counts = extract_kmers(seq, 4)
    k3_entropy = shannon_entropy(k3_counts)
    k4_entropy = shannon_entropy(k4_counts)
    
    # 5. Longest ORF Ratio
    longest_orf = 0
    stops = ["TAA", "TAG", "TGA"]
    stop_positions = [-1]
    for i in range(0, length - 2):
        if seq[i:i+3] in stops:
            stop_positions.append(i)
    stop_positions.append(length)
    
    for i in range(len(stop_positions) - 1):
        dist = stop_positions[i+1] - stop_positions[i] - 3
        if dist > longest_orf:
            longest_orf = dist
            
    longest_orf_ratio = max(0, longest_orf) / length
    
    # 6. Repeat Density
    repeats = 0
    for i in range(length - 4):
        if seq[i:i+2] == seq[i+2:i+4]:
            repeats += 1
    repeat_density = repeats / max(1, (length - 4))
    
    return {
        "gc_content": gc_content,
        "skew_gc": skew_gc,
        "skew_at": skew_at,
        "cpg_ratio": cpg_ratio,
        "complexity": complexity,
        "length": length,
        "kmer_3_entropy": k3_entropy,
        "kmer_4_entropy": k4_entropy,
        "longest_orf_ratio": longest_orf_ratio,
        "repeat_density": repeat_density
    }

def feature_dict_to_vector(features: dict) -> np.ndarray:
    """Convert feature dictionary to a numpy array for model input."""
    # Ensure consistent order - CRITICAL for Kaggle compatibility
    keys = ["gc_content", "skew_gc", "skew_at", "cpg_ratio", "complexity", "length", "kmer_3_entropy", "kmer_4_entropy", "longest_orf_ratio", "repeat_density"]
    return np.array([features[k] for k in keys])

FEATURE_NAMES = ["gc_content", "skew_gc", "skew_at", "cpg_ratio", "complexity", "length", "kmer_3_entropy", "kmer_4_entropy", "longest_orf_ratio", "repeat_density"]
