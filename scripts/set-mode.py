#!/usr/bin/env python3
"""Set DUCKBOTOS_MODE in src/args.sh"""
import sys
mode = sys.argv[1] if len(sys.argv) > 1 else "hermes"
with open("src/args.sh") as f:
    src = f.read()
src = src.replace('export DUCKBOTOS_MODE="hermes"', f'export DUCKBOTOS_MODE="{mode}"', 1)
with open("src/args.sh", "w") as f:
    f.write(src)
print(f"args.sh updated: DUCKBOTOS_MODE={mode}")
