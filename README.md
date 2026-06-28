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

1. En el repo: **Settings → Pages → Build and deployment → GitHub Actions**.
2. Push a `main` (o ejecutar el workflow manualmente).
3. El workflow `.github/workflows/pages.yml` renderiza todo con Quarto y publica `_site`.

Portada local:

```bash
quarto render index.qmd
# abre index.html
```

## Render

Desde la raíz del repo:

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

Los fragmentos HTML embebidos (`results_tables_embed.html`, `model_videos_embed.html`) están en `.gitignore`; el workflow de GitHub Pages los regenera antes del render.

## Estilos

Los estilos compartidos están en `_quarto.yml` y `assets/stylesheets/`:

| Archivo | Uso |
|---------|-----|
| `theme.scss` | Tema base TAR (labs y notas HTML) |
| `tar-lab.scss` | Ajustes menores de labs |
| `tar-index.scss` | Portada (`index.qmd`) |
| `tar-reveal.scss` | Presentación Reveal.js (RFHF) |
