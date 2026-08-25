"""Export the trained brain to fp16 for portable distribution.

The fp32 checkpoint (ckpt/last.pt) stays a training artifact. The fp16
file (ckpt/brain.fp16.pt) is the shippable product: half the size,
behaviorally identical for short-form generation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent


def export(src: Path | None = None, dst: Path | None = None) -> Path:
    src = src or ROOT / "ckpt" / "last.pt"
    dst = dst or ROOT / "ckpt" / "brain.fp16.pt"
    blob = torch.load(src, weights_only=False)
    fp16_state = {k: (v.half() if v.dtype == torch.float32 else v) for k, v in blob["model"].items()}
    torch.save(
        {"model": fp16_state, "cfg": blob["cfg"], "step": blob["step"], "dtype": "fp16"},
        dst,
    )
    before = src.stat().st_size / 1e6
    after = dst.stat().st_size / 1e6
    print(f"exported {before:.1f}MB -> {after:.1f}MB  ({dst})")
    return dst


if __name__ == "__main__":
    sys.exit(0 if export() else 1)
