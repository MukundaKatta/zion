"""CLI for zion."""
import sys, json, argparse
from .core import Zion

def main():
    parser = argparse.ArgumentParser(description="The Zion Boundary — Mapping the limits of human control over agentic AI. Adversarial robustness as humanity's last line of defense.")
    parser.add_argument("command", nargs="?", default="status", choices=["status", "run", "info"])
    parser.add_argument("--input", "-i", default="")
    args = parser.parse_args()
    instance = Zion()
    if args.command == "status":
        print(json.dumps(instance.get_stats(), indent=2))
    elif args.command == "run":
        print(json.dumps(instance.process(input=args.input or "test"), indent=2, default=str))
    elif args.command == "info":
        print(f"zion v0.1.0 — The Zion Boundary — Mapping the limits of human control over agentic AI. Adversarial robustness as humanity's last line of defense.")

if __name__ == "__main__":
    main()
