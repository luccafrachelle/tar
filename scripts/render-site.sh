#!/usr/bin/env bash
# Genera site/ para GitHub Pages (un .html autocontenido por página).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/.venv/bin/python"
[[ -x "$PY" ]] || PY=python3

render() {
  local dir="$1" qmd="$2" out="$3"
  local stem="${qmd%.qmd}"
  echo "→ $dir/$qmd → site/$out"
  mkdir -p "$(dirname "$ROOT/site/$out")"
  (
    cd "$ROOT/$dir"
    quarto render "$qmd"
    mv "$stem.html" "$ROOT/site/$out"
    rm -rf "${stem}_files"
  )
}

rm -rf site
mkdir -p site/labs
touch site/.nojekyll

$PY labs/lab4/scripts/lab4_pregunta3_tables.py
$PY labs/lab4/scripts/lab4_pregunta3_videos.py --html-only --skip-existing

render "." index.qmd index.html
render "labs/lab1" Lab1.qmd labs/lab1.html
render "labs/lab2" Lab2.qmd labs/lab2.html
render "labs/lab3" Lab3.qmd labs/lab3.html
render "labs/lab4" Lab4.qmd labs/lab4.html
render "entrega/rfhf" RFHF.qmd slides.html
render "entrega/rfhf" RLHF-Notas.qmd notas.html

find site -type d -name interactive -exec rm -rf {} + 2>/dev/null || true
rm -rf site/assets Lab*_files index_files 2>/dev/null || true

echo "Listo: site/index.html + site/labs/*.html + notas/slides"
