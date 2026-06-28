#!/usr/bin/env bash
# Renderiza todo el sitio para GitHub Pages (correr desde la raíz del repo).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .venv/bin/python ]]; then
  PY=.venv/bin/python
else
  PY=python3
fi

echo "== Lab 4: fragmentos embebidos =="
$PY labs/lab4/scripts/lab4_pregunta3_tables.py
$PY labs/lab4/scripts/lab4_pregunta3_videos.py --html-only --skip-existing

echo "== Quarto =="
quarto render index.qmd
quarto render labs/lab1/Lab1.qmd
quarto render labs/lab2/Lab2.qmd
quarto render labs/lab3/Lab3.qmd
quarto render labs/lab4/Lab4.qmd
quarto render entrega/rfhf/RFHF.qmd
quarto render entrega/rfhf/RLHF-Notas.qmd

echo "Listo. Commiteá index.html, labs/**/*.html, entrega/**/*.html y carpetas *_files/."
