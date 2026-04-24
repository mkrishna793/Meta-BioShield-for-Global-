import os
from Bio import SeqIO

from bioshield.config import Config
from bioshield.verdict import VerdictEngine, FinalVerdict
from bioshield.screeners.kmer_screener import KmerScreener
from bioshield.screeners.ml_screener import MLScreener
from bioshield.screeners.protein_impact import ProteinImpactScreener

class BioShieldPipeline:
    """Orchestrates the multi-layered screening process."""
    
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

    def screen_sequence(self, sequence: str, seq_id: str) -> FinalVerdict:
        """Screen a single sequence through all active layers."""
        results = []
        for screener in self.screeners:
            try:
                res = screener.screen(sequence, seq_id)
                results.append(res)
            except Exception as e:
                print(f"Error running {screener.name} on {seq_id}: {e}")
                
        return VerdictEngine.aggregate(seq_id, results)

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
