import os
from Bio import SeqIO

from bioshield.config import Config
from bioshield.verdict import VerdictEngine, FinalVerdict
from bioshield.screeners.base import ScreenResult, Verdict
from bioshield.screeners.kmer_screener import KmerScreener
from bioshield.screeners.ml_screener import MLScreener
from bioshield.screeners.protein_impact import ProteinImpactScreener
from bioshield.screeners.codon_bias import CodonBiasScreener
from bioshield.screeners.cleavage_sites import CleavageSiteScreener
from bioshield.screeners.rna_folding import RNAFoldingScreener

SHORT_SEQ_THRESHOLD = 100
WINDOW_SIZE = 500
WINDOW_STEP = 250

MICRO_TRIGGERS = {
    "anthrax_PA_core": "ATGAAAAAACGGAGTTAT",
    "ebola_GP_start":  "ATGGGCGTTACAGGAATATTG",
    "ricin_A_core":    "ATGGATCCGAGGATCTTTG",
    "botox_light":     "ATGCCAGTTGTCAAAATGCCG",
    "smallpox_crmB":   "ATGACATCAGATGAAGATG",
}


class BioShieldPipeline:
    """
    6-Layer Defense-in-Depth DNA Screening Pipeline.
    
    Layer 1: K-mer Fingerprinting (statistical distribution)
    Layer 2: ML Ensemble + Meta-Learner (RF + XGB + Logistic Regression)
    Layer 3: Protein Impact + ESM-2 Embeddings (functional shape)
    Layer 4: Host Codon Bias (human codon optimization detection)
    Layer 5: Protease Cleavage Sites (activation switch motifs)
    Layer 6: RNA Secondary Structure (folding potential analysis)
    
    Security features:
      - Sliding Window: defeats Trojan Horse dilution attacks
      - Bifurcated Pipeline: defeats split-order micro-sequence attacks
      - Canonical K-mers: defeats reverse-complement evasion
    """
    
    def __init__(self, config_path: str = "bioshield-config.yaml"):
        self.config = Config(config_path)
        self.screeners = []
        self._initialize_screeners()
        
    def _initialize_screeners(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Layer 1: K-mer Fingerprinting
        if self.config.get("pipeline.run_kmer", True):
            db_path = os.path.join(base_dir, self.config.get("kmer_screener.db_path", "bioshield/data/threat_kmers.json"))
            self.screeners.append(KmerScreener(
                db_path=db_path,
                threshold=self.config.get("kmer_screener.threshold", 0.85)
            ))
            
        # Layer 2: ML Ensemble + Meta-Learner
        if self.config.get("pipeline.run_ml", True):
            rf_path = os.path.join(base_dir, self.config.get("ml_screener.rf_model_path", "bioshield/ml/models/rf_model.joblib"))
            xgb_path = os.path.join(base_dir, self.config.get("ml_screener.xgb_model_path", "bioshield/ml/models/xgb_model.joblib"))
            meta_path = os.path.join(base_dir, self.config.get("ml_screener.meta_model_path", "bioshield/ml/models/meta_learner.joblib"))
            self.screeners.append(MLScreener(
                rf_path=rf_path,
                xgb_path=xgb_path,
                meta_path=meta_path,
                threshold=self.config.get("ml_screener.threshold", 0.70)
            ))
            
        # Layer 3: Protein Impact + ESM-2
        if self.config.get("pipeline.run_protein_impact", True):
            db_path = os.path.join(base_dir, self.config.get("protein_impact.db_path", "bioshield/data/uniprot_toxins.json"))
            self.screeners.append(ProteinImpactScreener(
                db_path=db_path,
                min_orf_length=self.config.get("protein_impact.min_orf_length", 100),
                identity_threshold=self.config.get("protein_impact.identity_threshold", 40.0)
            ))

        # Layer 4: Codon Bias
        if self.config.get("pipeline.run_codon_bias", True):
            self.screeners.append(CodonBiasScreener(
                threshold=self.config.get("codon_bias.threshold", 0.75)
            ))

        # Layer 5: Cleavage Sites
        if self.config.get("pipeline.run_cleavage_sites", True):
            self.screeners.append(CleavageSiteScreener())

        # Layer 6: RNA Folding
        if self.config.get("pipeline.run_rna_folding", True):
            self.screeners.append(RNAFoldingScreener(
                palindrome_threshold=self.config.get("rna_folding.palindrome_threshold", 0.15)
            ))

    def _screen_micro_sequence(self, sequence: str, seq_id: str) -> FinalVerdict:
        """Bifurcated Pipeline for ultra-short sequences (<100bp)."""
        seq_upper = sequence.upper()
        matches = []
        
        for trigger_name, trigger_seq in MICRO_TRIGGERS.items():
            if trigger_seq in seq_upper:
                matches.append((trigger_name, "forward"))
            from bioshield.utils.sequence import reverse_complement
            rc = reverse_complement(trigger_seq)
            if rc in seq_upper:
                matches.append((trigger_name, "reverse_complement"))
        
        if matches:
            match_names = [f"{m[0]}({m[1]})" for m in matches]
            result = ScreenResult(
                layer_name="MicroSequenceScreener", flagged=True, confidence=1.0,
                explanation=f"CRITICAL: Short sequence matches {len(matches)} trigger motif(s): {', '.join(match_names)}. "
                            f"Possible split-order attack.",
                details={"matches": match_names, "mode": "micro_trigger_search"}
            )
        else:
            result = ScreenResult(
                layer_name="MicroSequenceScreener", flagged=False, confidence=1.0,
                explanation=f"Short sequence ({len(sequence)}bp) cleared micro-trigger database ({len(MICRO_TRIGGERS)} motifs checked).",
                details={"mode": "micro_trigger_search", "motifs_checked": len(MICRO_TRIGGERS)}
            )
        
        return VerdictEngine.aggregate(seq_id, [result])

    def _screen_single_chunk(self, sequence: str, seq_id: str) -> list:
        """Screen a single chunk through all active layers."""
        results = []
        for screener in self.screeners:
            try:
                res = screener.screen(sequence, seq_id)
                results.append(res)
            except Exception as e:
                print(f"Error running {screener.name} on {seq_id}: {e}")
        return results

    def screen_sequence(self, sequence: str, seq_id: str) -> FinalVerdict:
        """Screen a single sequence through the full 6-layer pipeline."""
        length = len(sequence)
        
        if length < SHORT_SEQ_THRESHOLD:
            return self._screen_micro_sequence(sequence, seq_id)
        
        if length > WINDOW_SIZE:
            return self._screen_with_sliding_window(sequence, seq_id)
        
        results = self._screen_single_chunk(sequence, seq_id)
        return VerdictEngine.aggregate(seq_id, results)

    def _screen_with_sliding_window(self, sequence: str, seq_id: str) -> FinalVerdict:
        """Sliding Window Architecture for long sequences."""
        windows = []
        for start in range(0, len(sequence) - WINDOW_SIZE + 1, WINDOW_STEP):
            windows.append(sequence[start:start + WINDOW_SIZE])
        if len(sequence) % WINDOW_STEP != 0:
            windows.append(sequence[-WINDOW_SIZE:])
        
        worst_per_layer = {}
        
        for win_idx, window in enumerate(windows):
            win_results = self._screen_single_chunk(window, f"{seq_id}_win{win_idx}")
            for result in win_results:
                layer = result.layer_name
                if layer not in worst_per_layer:
                    worst_per_layer[layer] = result
                else:
                    existing = worst_per_layer[layer]
                    if result.flagged and not existing.flagged:
                        worst_per_layer[layer] = result
                    elif result.flagged and existing.flagged:
                        if result.confidence > existing.confidence:
                            worst_per_layer[layer] = result
        
        final_results = []
        for layer_name, result in worst_per_layer.items():
            result.explanation = f"[Windowed: {len(windows)} chunks] " + result.explanation
            final_results.append(result)
        
        return VerdictEngine.aggregate(seq_id, final_results)

    def screen_fasta(self, fasta_path: str) -> list[FinalVerdict]:
        """Screen all sequences in a FASTA file."""
        if not os.path.exists(fasta_path):
            raise FileNotFoundError(f"FASTA file not found: {fasta_path}")
        verdicts = []
        with open(fasta_path, "r") as handle:
            for record in SeqIO.parse(handle, "fasta"):
                verdict = self.screen_sequence(str(record.seq), record.id)
                verdicts.append(verdict)
        return verdicts
