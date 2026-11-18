"""Rename the original observations journal to preserve the v0 artifact.

WARNING: Mutates filesystem state; intended for a one-time migration."""

import os

os.rename("observations.jsonl", "observations-v0.jsonl")
print("Original journal archived")