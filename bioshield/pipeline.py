import os
from Bio import SeqIO

from bioshield.config import Config
from bioshield.verdict import VerdictEngine, FinalVerdict
from bioshield.screeners.base import ScreenResult, Verdict
from bioshield.screeners.kmer_screener import KmerScreener
from bioshield.screeners.ml_screener import MLScreener
from bioshield.screeners.protein_impact import ProteinImpactScreener

# Minimum sequence length for meaningful k-mer/ML analysis
SHORT_SEQ_THRESHOLD = 100

# Sliding window parameters
WINDOW_SIZE = 500
WINDOW_STEP = 250  # 50% overlap

# Critical short trigger sequences (20-30bp minimum functional motifs)
# These are the absolute bare-minimum sequences required for pathogen function.
# A real production system would have thousands; these demonstrate the concept.
MICRO_TRIGGERS = {
    "anthrax_PA_core": "ATGAAAAAACGGAGTTAT",       # Anthrax protective antigen signal
    "ebola_GP_start":  "ATGGGCGTTACAGGAATATTG",    # Ebola GP initiation
    "ricin_A_core":    "ATGGATCCGAGGATCTTTG",       # Ricin A-chain signal
    "botox_light":     "ATGCCAGTTGTCAAAATGCCG",     # Botulinum light chain start
    "smallpox_crmB":   "ATGACATCAGATGAAGATG",       # Variola CrmB immune evasion
}


class BioShieldPipeline:
    """
    Orchestrates the multi-layered screening process.
    
    Architecture improvements:
      - Sliding Window: Long sequences are chopped into overlapping windows.
        If ANY window flags, the whole sequence is flagged. This defeats the
        "Trojan Horse" dilution attack where a tiny threat hides in safe DNA.
      - Bifurcated Pipeline: Ultra-short sequences (<100bp) bypass K-mer/ML
        (which produce noisy results at that length) and instead go through
        an exhaustive micro-trigger database search.
    """
    
    def __init__(self, config_path: str = "bioshield-config.yaml"):
        self.config = Config(config_path)
        self.screeners = []
        self._initialize_screeners()
        
    def _initialize_screeners(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if self.config.get("pipeline.run_kmer", True):
            db_path = os.path.join(base_dir, self.config.get("kmer_screener.db_path", "bioshield/data/threat_kmers.json"))
            self.screeners.append(KmerScreener(
                db_path=db_path,
                threshold=self.config.get("kmer_screener.threshold", 0.85)
            ))
            
        if self.config.get("pipeline.run_ml", True):
            rf_path = os.path.join(base_dir, self.config.get("ml_screener.rf_model_path", "bioshield/ml/models/rf_model.joblib"))
            xgb_path = os.path.join(base_dir, self.config.get("ml_screener.xgb_model_path", "bioshield/ml/models/xgb_model.joblib"))
            self.screeners.append(MLScreener(
                rf_path=rf_path,
                xgb_path=xgb_path,
                threshold=self.config.get("ml_screener.threshold", 0.70)
            ))
            
        if self.config.get("pipeline.run_protein_impact", True):
            db_path = os.path.join(base_dir, self.config.get("protein_impact.db_path", "bioshield/data/uniprot_toxins.json"))
            self.screeners.append(ProteinImpactScreener(
                db_path=db_path,
                min_orf_length=self.config.get("protein_impact.min_orf_length", 100),
                identity_threshold=self.config.get("protein_impact.identity_threshold", 40.0)
            ))

    def _screen_micro_sequence(self, sequence: str, seq_id: str) -> FinalVerdict:
        """
        Fix #3: Bifurcated Pipeline for ultra-short sequences (<100bp).
        Standard k-mer/ML analysis breaks down at this length.
        Instead, do exhaustive exact-match against critical trigger motifs.
        """
        seq_upper = sequence.upper()
        matches = []
        
        for trigger_name, trigger_seq in MICRO_TRIGGERS.items():
            # Check forward strand
            if trigger_seq in seq_upper:
                matches.append((trigger_name, "forward"))
            # Check reverse complement
            from bioshield.utils.sequence import reverse_complement
            rc = reverse_complement(trigger_seq)
            if rc in seq_upper:
                matches.append((trigger_name, "reverse_complement"))
        
        if matches:
            match_names = [f"{m[0]}({m[1]})" for m in matches]
            result = ScreenResult(
                layer_name="MicroSequenceScreener",
                flagged=True,
                confidence=1.0,
                explanation=f"CRITICAL: Short sequence matches {len(matches)} trigger motif(s): {', '.join(match_names)}. "
                            f"Possible split-order attack (ordering a pathogen in many small pieces).",
                details={"matches": match_names, "mode": "micro_trigger_search"}
            )
        else:
            result = ScreenResult(
                layer_name="MicroSequenceScreener",
                flagged=False,
                confidence=1.0,
                explanation=f"Short sequence ({len(sequence)}bp) cleared micro-trigger database ({len(MICRO_TRIGGERS)} motifs checked).",
                details={"mode": "micro_trigger_search", "motifs_checked": len(MICRO_TRIGGERS)}
            )
        
        return VerdictEngine.aggregate(seq_id, [result])

    def _screen_single_chunk(self, sequence: str, seq_id: str) -> list:
        """Screen a single chunk through all active layers. Returns list of ScreenResults."""
        results = []
        for screener in self.screeners:
            try:
                res = screener.screen(sequence, seq_id)
                results.append(res)
            except Exception as e:
                print(f"Error running {screener.name} on {seq_id}: {e}")
        return results

    def screen_sequence(self, sequence: str, seq_id: str) -> FinalVerdict:
        """
        Screen a single sequence through the full pipeline.
        
        Routing logic:
          - If len < 100bp: Route to MicroSequenceScreener (Fix #3)
          - If len > WINDOW_SIZE: Use Sliding Window (Fix #1)
          - Otherwise: Standard full-pipeline screening
        """
        length = len(sequence)
        
        # --- Fix #3: Bifurcated Pipeline for short sequences ---
        if length < SHORT_SEQ_THRESHOLD:
            return self._screen_micro_sequence(sequence, seq_id)
        
        # --- Fix #1: Sliding Window for long sequences ---
        if length > WINDOW_SIZE:
            return self._screen_with_sliding_window(sequence, seq_id)
        
        # --- Standard screening for medium sequences ---
        results = self._screen_single_chunk(sequence, seq_id)
        return VerdictEngine.aggregate(seq_id, results)

    def _screen_with_sliding_window(self, sequence: str, seq_id: str) -> FinalVerdict:
        """
        Fix #1: Sliding Window Architecture.
        Chops the sequence into overlapping windows and screens each independently.
        If ANY window flags on ANY layer, the whole sequence is flagged for that layer.
        This defeats the "Trojan Horse" dilution attack.
        """
        windows = []
        for start in range(0, len(sequence) - WINDOW_SIZE + 1, WINDOW_STEP):
            windows.append(sequence[start:start + WINDOW_SIZE])
        # Include the tail if it wasn't fully covered
        if len(sequence) % WINDOW_STEP != 0:
            windows.append(sequence[-WINDOW_SIZE:])
        
        # Track the worst result per layer across ALL windows
        worst_per_layer = {}  # layer_name -> ScreenResult (keep the most flagged/highest prob)
        
        for win_idx, window in enumerate(windows):
            win_results = self._screen_single_chunk(window, f"{seq_id}_win{win_idx}")
            
            for result in win_results:
                layer = result.layer_name
                if layer not in worst_per_layer:
                    worst_per_layer[layer] = result
                else:
                    existing = worst_per_layer[layer]
                    # Keep the MORE dangerous result
                    if result.flagged and not existing.flagged:
                        worst_per_layer[layer] = result
                    elif result.flagged and existing.flagged:
                        # Both flagged: keep higher confidence (more certain threat)
                        if result.confidence > existing.confidence:
                            worst_per_layer[layer] = result
        
        # Annotate the winning results with window info
        final_results = []
        for layer_name, result in worst_per_layer.items():
            # Mark that this was a windowed analysis
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
                seq_id = record.id
                sequence = str(record.seq)
                verdict = self.screen_sequence(sequence, seq_id)
                verdicts.append(verdict)
                
        return verdicts
