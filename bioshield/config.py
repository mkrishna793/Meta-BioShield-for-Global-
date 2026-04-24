import yaml
import os

class Config:
    def __init__(self, config_path: str = "bioshield-config.yaml"):
        self.config_path = config_path
        self.settings = self._load()
        
    def _load(self):
        if not os.path.exists(self.config_path):
            print(f"Warning: Config file {self.config_path} not found. Using defaults.")
            return {}
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def get(self, key: str, default=None):
        keys = key.split('.')
        val = self.settings
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val
