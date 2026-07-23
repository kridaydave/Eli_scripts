from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
PROCESSED = ROOT / "processed"

DESIGN_SYSTEMS = RAW / "design-systems"
CODEPEN = RAW / "codepen"
GITHUB = RAW / "github"
GITHUB_BACKEND = GITHUB / "backend"
GITHUB_FRONTEND = GITHUB / "frontend"

DATA = ROOT / "data"
ELI_PAIRS = DATA / "eli-training-pairs.txt"

TRAINING_OUT = PROCESSED / "training-data.jsonl"

