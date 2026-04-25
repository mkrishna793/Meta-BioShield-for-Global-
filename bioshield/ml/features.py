import numpy as np
from collections import Counter
import math
import zlib
from bioshield.utils.sequence import extract_kmers, extract_canonical_kmers, reverse_complement

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
    """
    Extract machine learning features from a DNA sequence.
    Uses CANONICAL k-mers (strand-agnostic) and combines forward+reverse
    complement features to defeat the reverse-complement evasion attack.
    """
    seq = seq.upper()
    length = len(seq)
    
    if length == 0:
        return {k: 0.0 for k in FEATURE_NAMES}
    
    # Compute reverse complement once
    rc_seq = reverse_complement(seq)
    
    # 1. GC Content & Skews (strand-symmetric: combine forward + reverse)
    a = seq.count('A')
    t = seq.count('T')
    g = seq.count('G')
    c = seq.count('C')
    gc_content = (g + c) / length
    
    # For skews, average forward and reverse to make strand-agnostic
    fwd_skew_gc = (g - c) / max(1, (g + c))
    fwd_skew_at = (a - t) / max(1, (a + t))
    
    rc_a, rc_t, rc_g, rc_c = rc_seq.count('A'), rc_seq.count('T'), rc_seq.count('G'), rc_seq.count('C')
    rc_skew_gc = (rc_g - rc_c) / max(1, (rc_g + rc_c))
    rc_skew_at = (rc_a - rc_t) / max(1, (rc_a + rc_t))
    
    # Take absolute value of the average to get strand-agnostic magnitude
    skew_gc = abs(fwd_skew_gc + rc_skew_gc) / 2
    skew_at = abs(fwd_skew_at + rc_skew_at) / 2
    
    # 2. CpG Dinucleotide Ratio (Key for catching synthetic DNA)
    cg_count = seq.count('CG')
    expected_cg = (c * g) / max(1, length)
    cpg_ratio = cg_count / expected_cg if expected_cg > 0 else 0.0
    
    # 3. Sequence Complexity (zlib compression ratio)
    compressed_len = len(zlib.compress(seq.encode('utf-8')))
    complexity = compressed_len / max(1, length)
    
    # 4. CANONICAL K-mer Entropies (strand-agnostic: counts ATGC same as GCAT)
    k3_counts = extract_canonical_kmers(seq, 3)
    k4_counts = extract_canonical_kmers(seq, 4)
    k3_entropy = shannon_entropy(k3_counts)
    k4_entropy = shannon_entropy(k4_counts)
    
    # 5. Longest ORF Ratio (check BOTH strands, take the max)
    def _longest_orf_ratio(s):
        slen = len(s)
        stops = ["TAA", "TAG", "TGA"]
        stop_positions = [-1]
        for i in range(0, slen - 2):
            if s[i:i+3] in stops:
                stop_positions.append(i)
        stop_positions.append(slen)
        longest = 0
        for i in range(len(stop_positions) - 1):
            dist = stop_positions[i+1] - stop_positions[i] - 3
            if dist > longest:
                longest = dist
        return max(0, longest) / max(1, slen)
    
    fwd_orf = _longest_orf_ratio(seq)
    rc_orf = _longest_orf_ratio(rc_seq)
    longest_orf_ratio = max(fwd_orf, rc_orf)
    
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
    return np.array([features[k] for k in FEATURE_NAMES])

FEATURE_NAMES = [
    "gc_content", "skew_gc", "skew_at", "cpg_ratio", "complexity",
    "length", "kmer_3_entropy", "kmer_4_entropy", "longest_orf_ratio", "repeat_density"
]
