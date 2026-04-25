from collections import Counter
import numpy as np
from Bio.Seq import Seq

# Complement table for reverse-complement computation
_COMPLEMENT = str.maketrans('ACGT', 'TGCA')

def reverse_complement(seq: str) -> str:
    """Return the reverse complement of a DNA sequence."""
    return seq.upper().translate(_COMPLEMENT)[::-1]

def canonical_kmer(kmer: str) -> str:
    """
    Return the canonical (lexicographically smaller) form of a k-mer.
    This ensures that a k-mer and its reverse-complement are counted as the same thing.
    Critical for defeating the reverse-complement evasion attack.
    """
    rc = reverse_complement(kmer)
    return min(kmer, rc)

def extract_kmers(seq: str, k: int) -> Counter:
    """Extract all overlapping k-mers from a sequence."""
    seq = seq.upper()
    kmers = [seq[i:i+k] for i in range(len(seq) - k + 1)]
    return Counter(kmers)

def extract_canonical_kmers(seq: str, k: int) -> Counter:
    """
    Extract canonical k-mers (strand-agnostic).
    Each k-mer is reduced to its lexicographically smaller form,
    so ATGC and GCAT (its reverse complement) are counted as one.
    """
    seq = seq.upper()
    kmers = []
    for i in range(len(seq) - k + 1):
        kmer = seq[i:i+k]
        kmers.append(canonical_kmer(kmer))
    return Counter(kmers)

def kmer_frequency_vector(seq: str, k: int, vocab: list[str] = None) -> np.ndarray:
    """
    Get normalized k-mer frequency vector.
    If vocab is provided, returns frequencies in the order of vocab.
    """
    kmers = extract_kmers(seq, k)
    total = sum(kmers.values())
    
    if total == 0:
        if vocab:
            return np.zeros(len(vocab))
        return np.array([])
        
    if vocab:
        vec = np.array([kmers.get(v, 0) for v in vocab], dtype=float)
        return vec / total
    else:
        # Without vocab, just return normalized frequencies of present k-mers
        # This is less useful for direct comparisons, but good for entropies
        vec = np.array(list(kmers.values()), dtype=float)
        return vec / total

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

def translate_all_frames(seq: str) -> list[str]:
    """Translate DNA sequence in all 6 reading frames."""
    dna_seq = Seq(seq.upper())
    rev_comp = dna_seq.reverse_complement()
    
    proteins = []
    # Forward frames
    for i in range(3):
        # Pad to multiple of 3
        frame_seq = dna_seq[i:]
        remainder = len(frame_seq) % 3
        if remainder:
            frame_seq = frame_seq[:-remainder]
        proteins.append(str(frame_seq.translate(to_stop=False)))
        
    # Reverse frames
    for i in range(3):
        frame_seq = rev_comp[i:]
        remainder = len(frame_seq) % 3
        if remainder:
            frame_seq = frame_seq[:-remainder]
        proteins.append(str(frame_seq.translate(to_stop=False)))
        
    return proteins

def find_orfs(protein_seq: str, min_length: int = 100) -> list[str]:
    """Find all Open Reading Frames (ORFs) separated by stop codons (*) >= min_length."""
    orfs = protein_seq.split('*')
    return [orf for orf in orfs if len(orf) >= min_length]
