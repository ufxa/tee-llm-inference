#!/bin/bash
# TwinGuard — LaTeX Build Script
# Compiler: tectonic (required)
# Usage: ./scripts/build.sh

set -e

PAPER_DIR="$(dirname "$0")/../paper"
cd "$PAPER_DIR"

echo "[TwinGuard] Building paper with tectonic..."
tectonic main.tex

echo "[TwinGuard] Build complete: paper/main.pdf"
