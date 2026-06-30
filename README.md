# TAR 2026 — Lucca Frachelle

Material del Taller de Aprendizaje por Refuerzo (Maestría).

## Publicar sitio

```bash
bash scripts/render-site.sh
git add site/
git commit -m "Actualizar sitio"
git push
```

GitHub Pages publica la carpeta `site/` (workflow en `.github/workflows/pages.yml`).

Cada página se renderiza con `embed-resources: true` (HTML único, sin carpetas `*_files/`).

## Estructura

```
index.qmd          portada
labs/lab*/Lab*.qmd laboratorios
entrega/rfhf/      slides y notas RLHF
site/              HTML publicado
_quarto.yml        estilos y embed-resources globales
```
