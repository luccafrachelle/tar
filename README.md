# TAR 2026 — Lucca Frachelle

Entregables del Taller de Aprendizaje por Refuerzo (Maestría).

## Estructura

```
tar/
├── index.qmd                # portada para GitHub Pages
├── _quarto.yml              # estilos y metadata compartidos
├── references.bib           # bibliografía común
├── assets/                  # CSS, scripts, imágenes compartidas
├── labs/
│   ├── lab1/                # MDP
│   ├── lab2/                # Q-learning / TD
│   ├── lab3/                # Actor-Critic + interactivos
│   └── lab4/                # PPO (roundabout + lane keeping)
│       ├── scripts/         # barrido P3, tablas, videos
│       └── results/         # figuras, modelos, videos Lab 4
└── entrega/
    └── rfhf/                # presentación + notas InstructGPT / RLHF
```

## GitHub Pages

Deploy **estático**: no se renderiza en CI, solo se publica el HTML ya generado.

1. En el repo: **Settings → Pages → Build and deployment → GitHub Actions**.
2. Renderizá localmente y commiteá el HTML:

```bash
bash scripts/render-site.sh
git add index.html index_files labs entrega
git commit -m "Actualizar sitio renderizado"
git push
```

3. El workflow `.github/workflows/pages.yml` copia `index.html`, `assets/`, `labs/` y `entrega/` a Pages.

## Render manual

Desde la raíz del repo (o `bash scripts/render-site.sh` para todo junto):

```bash
# Portada
quarto render index.qmd

# Labs
quarto render labs/lab1/Lab1.qmd
quarto render labs/lab2/Lab2.qmd
quarto render labs/lab3/Lab3.qmd
quarto render labs/lab4/Lab4.qmd

# Entrega RFHF
quarto render entrega/rfhf/RFHF.qmd
quarto render entrega/rfhf/RLHF-Notas.qmd
```

Lab 4 — regenerar experimentos Pregunta 3:

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
