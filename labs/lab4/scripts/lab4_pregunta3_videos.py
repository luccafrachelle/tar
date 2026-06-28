#!/usr/bin/env python3
"""
Genera un video por cada modelo PPO del barrido (Pregunta 3) y un reproductor HTML
con botones para cambiar entre ellos (un solo video visible a la vez).

Salida:
    labs/lab4/results/pregunta3/videos/*.mp4
    labs/lab4/results/pregunta3/model_videos.html          (página standalone)
    labs/lab4/results/pregunta3/model_videos_embed.html    (fragmento para Lab4.qmd)

Uso:
    python scripts/lab4_pregunta3_videos.py
    python scripts/lab4_pregunta3_videos.py --skip-existing
    python scripts/lab4_pregunta3_videos.py --html-only --skip-existing
"""

from __future__ import annotations

import argparse
import base64
import json
import warnings
from pathlib import Path

import gymnasium as gym
import highway_env  # noqa: F401
import imageio
from stable_baselines3 import PPO

warnings.filterwarnings("ignore", category=DeprecationWarning)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "pregunta3"
VIDEOS_DIR = OUT_DIR / "videos"
MODELS_DIR = OUT_DIR / "models"
RESULTS_PATH = OUT_DIR / "results.json"
HTML_PATH = OUT_DIR / "model_videos.html"
EMBED_PATH = OUT_DIR / "model_videos_embed.html"

RENDER_SEED = 42
FPS = 6
RECORD_DURATION = 40  # s de simulación (default del env: 11); muestra salida de la rotonda
MAX_STEPS = RECORD_DURATION + 5
PLAYER_ID = "rb-player"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument(
        "--html-only",
        action="store_true",
        help="Solo regenerar HTML (asume que los mp4 ya existen).",
    )
    return p.parse_args()


def load_results() -> list[dict]:
    return json.loads(RESULTS_PATH.read_text())


def record_episode(model_path: Path, video_path: Path) -> int:
    env = gym.make("roundabout-v0", render_mode="rgb_array")
    env.unwrapped.configure({"duration": RECORD_DURATION})
    model = PPO.load(str(model_path))
    obs, _ = env.reset(seed=RENDER_SEED)
    frames: list = []

    for _ in range(MAX_STEPS):
        action, _ = model.predict(obs, deterministic=True)
        obs, _, terminated, truncated, _ = env.step(action)
        frame = env.render()
        if frame is not None:
            frames.append(frame)
        if truncated:
            break

    env.close()
    video_path.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(
        video_path,
        frames,
        fps=FPS,
        codec="libx264",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )
    return len(frames)


def video_data_url(path: Path) -> str:
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:video/mp4;base64,{payload}"


def fmt_pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def build_css_only_player(entries: list[dict], *, standalone: bool) -> str:
    """Reproductor sin JavaScript (radios + CSS). Funciona embebido en Quarto."""
    n = len(entries)
    css_rules = [
        ".rb-wrap { --rb-border:#dde3ea; --rb-muted:#5c6570; --rb-accent:#2563eb;",
        "  --rb-accent-soft:#dbeafe; --rb-ok:#15803d; --rb-ok-bg:#dcfce7;",
        "  --rb-bad:#b91c1c; --rb-bad-bg:#fee2e2; max-width:980px; margin:.5rem 0 1.5rem; }",
        ".rb-wrap .rb-input { position:absolute; opacity:0; width:0; height:0; pointer-events:none; }",
        ".rb-wrap .rb-panel { display:none; }",
        ".rb-wrap .rb-player-card { background:var(--bs-body-bg,#fff); border:1px solid var(--rb-border);",
        "  border-radius:12px; padding:1rem; margin:.85rem 0; box-shadow:0 1px 3px rgba(0,0,0,.06); }",
        ".rb-wrap video { width:100%; max-height:520px; border-radius:8px; background:#111; display:block; }",
        ".rb-wrap .rb-meta { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr));",
        "  gap:.6rem 1rem; margin-top:.85rem; font-size:.88rem; }",
        ".rb-wrap .rb-meta dt { color:var(--rb-muted); font-size:.78rem; text-transform:uppercase;",
        "  letter-spacing:.03em; }",
        ".rb-wrap .rb-meta dd { margin:.1rem 0 0; font-weight:600; }",
        ".rb-wrap .rb-badge { display:inline-block; padding:.15rem .55rem; border-radius:999px;",
        "  font-size:.78rem; font-weight:600; }",
        ".rb-wrap .rb-badge.ok { background:var(--rb-ok-bg); color:var(--rb-ok); }",
        ".rb-wrap .rb-badge.bad { background:var(--rb-bad-bg); color:var(--rb-bad); }",
        ".rb-wrap .rb-controls-label { font-size:.85rem; font-weight:600; margin:0 0 .6rem; }",
        ".rb-wrap .rb-btn-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(118px,1fr)); gap:.45rem; }",
        ".rb-wrap .rb-model-btn { display:block; border:1px solid var(--rb-border); background:var(--bs-body-bg,#fff);",
        "  color:inherit; border-radius:8px; padding:.45rem .35rem; font-size:.8rem; cursor:pointer;",
        "  text-align:center; line-height:1.25; transition:border-color .15s,background .15s,box-shadow .15s; }",
        ".rb-wrap .rb-model-btn:hover { border-color:var(--rb-accent); background:var(--rb-accent-soft); }",
        ".rb-wrap .rb-model-btn .h { display:block; font-weight:700; font-size:.88rem; }",
        ".rb-wrap .rb-model-btn .t { display:block; color:var(--rb-muted); font-size:.74rem; }",
        ".rb-wrap .rb-model-btn .dot { display:inline-block; width:7px; height:7px; border-radius:50%;",
        "  margin-right:3px; vertical-align:middle; }",
        ".rb-wrap .rb-model-btn .dot.ok { background:var(--rb-ok); }",
        ".rb-wrap .rb-model-btn .dot.bad { background:var(--rb-bad); }",
    ]
    for i in range(n):
        css_rules.append(f"#rb-p-{i}:checked ~ .rb-panels .rb-panel-{i} {{ display:block; }}")
        css_rules.append(
            f"#rb-p-{i}:checked ~ .rb-btn-grid label[for='rb-p-{i}'] {{"
            f" border-color:var(--rb-accent); background:var(--rb-accent-soft);"
            f" box-shadow:0 0 0 2px rgba(37,99,235,.25); font-weight:650; }}"
        )

    radios = []
    labels = []
    panels = []
    for i, e in enumerate(entries):
        checked = " checked" if i == 0 else ""
        radios.append(f'<input type="radio" name="rb-player" id="rb-p-{i}" class="rb-input"{checked}>')
        ok_cls = "ok" if e["success"] else "bad"
        ok_txt = "OK" if e["success"] else "—"
        labels.append(
            f'<label for="rb-p-{i}" class="rb-model-btn">'
            f'<span class="h">H={e["hidden"]}</span>'
            f'<span class="t">T={e["timesteps"]:,}</span>'
            f'<span class="t"><span class="dot {ok_cls}"></span>{ok_txt}</span>'
            f"</label>"
        )
        badge = (
            '<span class="rb-badge ok">Resuelve</span>'
            if e["success"]
            else '<span class="rb-badge bad">No resuelve</span>'
        )
        video_src = e["video"]
        panels.append(
            f'<div class="rb-panel rb-panel-{i}">'
            f'<div class="rb-player-card">'
            f'<video controls playsinline preload="metadata" width="100%">'
            f'<source src="{video_src}" type="video/mp4">'
            f"</video>"
            f'<dl class="rb-meta">'
            f"<div><dt>Arquitectura</dt><dd>{e['arch']}</dd></div>"
            f"<div><dt>Timesteps</dt><dd>{e['timesteps']:,}</dd></div>"
            f"<div><dt>Recompensa (eval.)</dt><dd>{e['mean_reward']:.2f}</dd></div>"
            f"<div><dt>Choque</dt><dd>{fmt_pct(e['crash_rate'])}</dd></div>"
            f"<div><dt>Longitud</dt><dd>{e['mean_episode_length']:.1f} pasos</dd></div>"
            f"<div><dt>Resultado</dt><dd>{badge}</dd></div>"
            f"</dl></div></div>"
        )

    subtitle = ""
    if standalone:
        subtitle = (
            f'<p style="color:var(--rb-muted,#5c6570);font-size:.92rem;margin:0 0 .85rem;">'
            f"Un episodio determinista por configuración (semilla {RENDER_SEED}, "
            f"{RECORD_DURATION}&nbsp;s de simulación). Elegí un botón para cambiar el video.</p>"
        )

    return f"""<style>
{chr(10).join(css_rules)}
</style>
<div class="rb-wrap" id="{PLAYER_ID}">
  {subtitle}
  {''.join(radios)}
  <p class="rb-controls-label">Modelos entrenados ({n})</p>
  <div class="rb-btn-grid">
    {''.join(labels)}
  </div>
  <div class="rb-panels">
    {''.join(panels)}
  </div>
</div>
"""


def build_standalone_page(entries: list[dict]) -> str:
    body = build_css_only_player(entries, standalone=True)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pregunta 3 — Videos por modelo (roundabout-v0)</title>
</head>
<body style="margin:0;font-family:system-ui,sans-serif;background:#f8f9fb;">
  <div style="max-width:980px;margin:0 auto;padding:1.25rem 1rem 2rem;">
    <h1 style="font-size:1.25rem;margin:0 0 0.35rem;">Roundabout-v0 — comportamiento por modelo</h1>
    {body}
  </div>
</body>
</html>
"""


def build_embed_fragment(entries: list[dict]) -> str:
    return build_css_only_player(entries, standalone=False)


def collect_entries(results: list[dict], args: argparse.Namespace) -> list[dict]:
    html_entries: list[dict] = []

    for i, row in enumerate(results, 1):
        hidden = row["hidden"]
        timesteps = row["timesteps"]
        model_path = MODELS_DIR / f"ppo_H{hidden}_T{timesteps}.zip"
        video_name = f"H{hidden}_T{timesteps}.mp4"
        video_path = VIDEOS_DIR / video_name

        if not args.html_only:
            if not model_path.exists():
                print(f"[skip] modelo no encontrado: {model_path.name}")
                continue
            if args.skip_existing and video_path.exists():
                print(f"[skip] video existente: {video_name}")
            else:
                print(f"[{i}/{len(results)}] Grabando {video_name}…", flush=True)
                n_frames = record_episode(model_path, video_path)
                print(f"    → {n_frames} frames, {video_path.stat().st_size // 1024} KB")

        if not video_path.exists():
            print(f"[skip] video no encontrado: {video_name}")
            continue

        html_entries.append(
            {
                "id": f"H{hidden}_T{timesteps}",
                "hidden": hidden,
                "timesteps": timesteps,
                "arch": row["arch"],
                "mean_reward": row["mean_reward"],
                "crash_rate": row["crash_rate"],
                "mean_episode_length": row["mean_episode_length"],
                "success": row["success"],
                "video_file": f"videos/{video_name}",
            }
        )

    return html_entries


def main() -> None:
    args = parse_args()
    results = load_results()
    results.sort(key=lambda r: (r["hidden"], r["timesteps"]))

    base_entries = collect_entries(results, args)
    if not base_entries:
        raise SystemExit("No hay videos para embeber.")

    standalone_entries = [
        {**e, "video": e["video_file"]} for e in base_entries
    ]
    embed_entries = []
    print("Codificando videos en base64 para embeber en Lab4.qmd…")
    for e in base_entries:
        video_path = VIDEOS_DIR / Path(e["video_file"]).name
        embed_entries.append({**e, "video": video_data_url(video_path)})

    HTML_PATH.write_text(build_standalone_page(standalone_entries), encoding="utf-8")
    EMBED_PATH.write_text(build_embed_fragment(embed_entries), encoding="utf-8")

    embed_kb = EMBED_PATH.stat().st_size // 1024
    print(f"\nStandalone:  {HTML_PATH}")
    print(f"Embed:       {EMBED_PATH} ({embed_kb} KB)")
    print(f"Videos:      {VIDEOS_DIR}/ ({len(base_entries)} archivos)")


if __name__ == "__main__":
    main()
