# TAR 2026 — Lucca Frachelle

Entregables del Taller de Aprendizaje por Refuerzo (Maestría).

## Estructura

```
tar/
├── site/                    # HTML publicado (GitHub Pages)
│   ├── index.html
│   ├── lab1.html … lab4.html
│   ├── slides.html, notas.html
│   └── interactive/         # Plotly Lab 3
├── index.qmd                # fuente portada
├── _quarto.yml              # estilos y metadata compartidos
├── references.bib           # bibliografía común
├── assets/                  # CSS, scripts, imágenes compartidas
├── labs/                    # fuentes Quarto + resultados Lab 4
└── entrega/rfhf/            # fuentes RFHF / RLHF
```

## GitHub Pages

Deploy **estático** desde `site/` (sin render en CI).

1. **Settings → Pages → Build and deployment → GitHub Actions**
2. Generá y commiteá el sitio:

```bash
bash scripts/render-site.sh
git add site/
git commit -m "Actualizar sitio"
git push
```

3. El workflow publica `site/` tal cual.

Cada HTML usa `embed-resources: true` (archivo único, sin carpetas `*_files/`).

## Render manual (Quarto)

Desde cada carpeta fuente (o copiá el HTML a `site/`):

```bash
export QUARTO_PYTHON=/ruta/a/tu/.venv/bin/python   # Lab 4 necesita kernel autito-ppo

# Portada
quarto render index.qmd && mv index.html site/

# Labs
cd labs/lab1 && quarto render Lab1.qmd && cp Lab1.html ../../site/lab1.html
cd labs/lab2 && quarto render Lab2.qmd && cp Lab2.html ../../site/lab2.html
cd labs/lab3 && quarto render Lab3.qmd && cp Lab3.html ../../site/lab3.html
cd labs/lab4 && quarto render Lab4.qmd && cp Lab4.html ../../site/lab4.html

# RFHF
cd entrega/rfhf && quarto render RFHF.qmd && cp RFHF.html ../../site/slides.html
cd entrega/rfhf && quarto render RLHF-Notas.qmd && cp RLHF-Notas.html ../../site/notas.html

cp labs/lab3/interactive/*.html site/interactive/
```

Alternativa: `bash scripts/render-site.sh` (hace lo mismo en un paso).

Lab 4 — antes de renderizar, regenerá embeds Pregunta 3:

```bash
python labs/lab4/scripts/lab4_pregunta3_roundabout.py
python labs/lab4/scripts/lab4_pregunta3_videos.py
python labs/lab4/scripts/lab4_pregunta3_tables.py
```

Antes de renderizar Lab 4, generá los fragmentos embebidos con los dos primeros comandos de arriba (o usá `render-site.sh`).

## Estilos

Los estilos compartidos están en `_quarto.yml` y `assets/stylesheets/`:

| Archivo | Uso |
|---------|-----|
| `theme.scss` | Tema base TAR (labs y notas HTML) |
| `tar-lab.scss` | Ajustes menores de labs |
| `tar-index.scss` | Portada (`index.qmd`) |
| `tar-reveal.scss` | Presentación Reveal.js (RFHF) |
