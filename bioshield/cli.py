import argparse
import sys
import json
from bioshield.pipeline import BioShieldPipeline
from bioshield.ml.train import train_models

def print_verdict(verdict):
    color_reset = "\033[0m"
    color_red = "\033[91m"
    color_green = "\033[92m"
    color_yellow = "\033[93m"
    
    v_str = verdict.verdict.value
    if v_str == "PASS":
        color = color_green
    elif v_str == "FLAG":
        color = color_yellow
    else:
        color = color_red
        
    print(f"\n{'='*60}")
    print(f"Sequence ID: {verdict.sequence_id}")
    print(f"Verdict: {color}{v_str}{color_reset} (Confidence: {verdict.confidence:.2f})")
    print(f"{'-'*60}")
    
    for r in verdict.per_layer_results:
        l_color = color_red if r.flagged else color_green
        status = "FLAG" if r.flagged else "PASS"
        print(f"[{r.layer_name}] {l_color}{status}{color_reset}")
        print(f"  Explanation: {r.explanation}")
        
    print(f"{'='*60}\n")

def screen(args):
    try:
        pipeline = BioShieldPipeline(args.config)
        verdicts = pipeline.screen_fasta(args.fasta)
        
        if args.json:
            # Output as JSON
            output = []
            for v in verdicts:
                output.append({
                    "sequence_id": v.sequence_id,
                    "verdict": v.verdict.value,
                    "confidence": v.confidence,
                    "audit_trail": v.audit_trail,
                    "layer_details": [
                        {
                            "layer": r.layer_name,
                            "flagged": r.flagged,
                            "confidence": r.confidence,
                            "explanation": r.explanation,
                            "details": r.details
                        } for r in v.per_layer_results
                    ]
                })
            print(json.dumps(output, indent=2))
        else:
            for v in verdicts:
                print_verdict(v)
                
    except Exception as e:
        print(f"Error during screening: {e}")
        sys.exit(1)

def train(args):
    print("Training BioShield ML models...")
    train_models()

def main():
    parser = argparse.ArgumentParser(description="BioShield: Multi-Layered DNA Synthesis Screening")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Screen command
    screen_parser = subparsers.add_parser("screen", help="Screen a FASTA file")
    screen_parser.add_argument("fasta", help="Path to input FASTA file")
    screen_parser.add_argument("--config", default="bioshield-config.yaml", help="Path to config file")
    screen_parser.add_argument("--json", action="store_true", help="Output results as JSON")
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train ML models (generates mock data)")
    
    args = parser.parse_args()
    
    if args.command == "screen":
        screen(args)
    elif args.command == "train":
        train(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
