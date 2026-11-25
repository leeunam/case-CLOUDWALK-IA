"""Planeja e executa exclusivamente a rodada Luna R5."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from luna_r5.round_spec import LUNA_R5
from r2.execute import main


if __name__ == "__main__":
    main(LUNA_R5)
