#!/usr/bin/env bash
# Renderiza el sitio estático en site/ (GitHub Pages).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .venv/bin/python ]]; then
  PY=.venv/bin/python
else
  PY=python3
fi

# embed-resources: true falla con --output-dir (busca *_files en la raíz del repo).
# Renderizamos en el directorio del .qmd y movemos el HTML embebido a site/.
render_embed() {
  local src_dir="$1"
  local qmd="$2"
  local out_html="$3"
  local stem="${qmd%.qmd}"
  echo "  → $src_dir/$qmd → site/$out_html"
  (
    cd "$ROOT/$src_dir"
    quarto render "$qmd"
    mv "$stem.html" "$ROOT/site/$out_html"
    rm -rf "${stem}_files"
  )
}

rm -rf site
mkdir -p site

echo "== Lab 4: fragmentos embebidos =="
$PY labs/lab4/scripts/lab4_pregunta3_tables.py
$PY labs/lab4/scripts/lab4_pregunta3_videos.py --html-only --skip-existing

echo "== Quarto → site/ =="
render_embed "." index.qmd index.html
render_embed "labs/lab1" Lab1.qmd lab1.html
render_embed "labs/lab2" Lab2.qmd lab2.html
render_embed "labs/lab3" Lab3.qmd lab3.html
render_embed "labs/lab4" Lab4.qmd lab4.html
render_embed "entrega/rfhf" RFHF.qmd slides.html
render_embed "entrega/rfhf" RLHF-Notas.qmd notas.html

echo "== Lab 3: interactivos =="
mkdir -p site/interactive
cp labs/lab3/interactive/*.html site/interactive/

# Limpieza por si quedó basura de renders fallidos anteriores.
rm -rf site/assets site/labs site/entrega site/index_files 2>/dev/null || true
find site -maxdepth 1 -type d -name '*_files' -exec rm -rf {} + 2>/dev/null || true
rm -rf Lab1_files Lab2_files Lab3_files Lab4_files index_files 2>/dev/null || true

echo ""
echo "Sitio listo en site/:"
ls -lh site/*.html
echo ""
echo "Commiteá la carpeta site/ y hacé push."
