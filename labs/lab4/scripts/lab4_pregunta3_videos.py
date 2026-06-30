#!/usr/bin/env python3
"""
Genera videos por modelo PPO del barrido (Pregunta 3) en dos duraciones:
  - 11 s: horizonte de entrenamiento (recompensa del env)
  - 20 s: generalización más allá del episodio de entrenamiento

Salida:
    labs/lab4/results/pregunta3/videos/d11/*.mp4
    labs/lab4/results/pregunta3/videos/d20/*.mp4
    labs/lab4/results/pregunta3/model_videos_embed_d11.html
    labs/lab4/results/pregunta3/model_videos_embed_d20.html

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

warnings.filterwarnings("ignore", category=DeprecationWarning)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "pregunta3"
MODELS_DIR = OUT_DIR / "models"
RESULTS_PATH = OUT_DIR / "results.json"
EMBED_D11 = OUT_DIR / "model_videos_embed_d11.html"
EMBED_D20 = OUT_DIR / "model_videos_embed_d20.html"

RENDER_SEED = 42
FPS = 6
TRAIN_DURATION = 11
GENERALIZE_DURATION = 20

VIDEO_BLOCKS: tuple[tuple[int, str, Path, str], ...] = (
    (
        TRAIN_DURATION,
        "rb-player-d11",
        EMBED_D11,
        "Horizonte de entrenamiento (11 s): mismo `duration` del entorno y ventana donde se acumula recompensa.",
    ),
    (
        GENERALIZE_DURATION,
        "rb-player-d20",
        EMBED_D20,
        "Generalización (20 s): comportamiento al extender la simulación más allá del truncamiento habitual.",
    ),
)


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


def videos_dir(duration: int) -> Path:
    return OUT_DIR / "videos" / f"d{duration}"


def record_episode(model_path: Path, video_path: Path, *, duration: int) -> int:
    import gymnasium as gym
    import highway_env  # noqa: F401
    import imageio
    from stable_baselines3 import PPO

    env = gym.make("roundabout-v0", render_mode="rgb_array")
    env.unwrapped.configure({"duration": duration})
    model = PPO.load(str(model_path))
    obs, _ = env.reset(seed=RENDER_SEED)
    frames: list = []

    for _ in range(duration + 5):
        action, _ = model.predict(obs, deterministic=True)
        obs, _, terminated, truncated, _ = env.step(action)
        frame = env.render()
        if frame is not None:
            frames.append(frame)
        if truncated or terminated:
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


def build_css_only_player(
    entries: list[dict],
    *,
    standalone: bool,
    player_id: str,
    duration: int,
    blurb: str = "",
) -> str:
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
        ".rb-wrap .rb-blurb { color:var(--rb-muted,#5c6570); font-size:.9rem; margin:0 0 .75rem; line-height:1.45; }",
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
    radio_name = f"{player_id}-sel"
    for i in range(n):
        rid = f"{player_id}-p-{i}"
        css_rules.append(f"#{rid}:checked ~ .rb-panels .rb-panel-{i} {{ display:block; }}")
        css_rules.append(
            f"#{rid}:checked ~ .rb-btn-grid label[for='{rid}'] {{"
            f" border-color:var(--rb-accent); background:var(--rb-accent-soft);"
            f" box-shadow:0 0 0 2px rgba(37,99,235,.25); font-weight:650; }}"
        )

    radios = []
    labels = []
    panels = []
    for i, e in enumerate(entries):
        rid = f"{player_id}-p-{i}"
        checked = " checked" if i == 0 else ""
        radios.append(
            f'<input type="radio" name="{radio_name}" id="{rid}" class="rb-input"{checked}>'
        )
        ok_cls = "ok" if e["success"] else "bad"
        ok_txt = "OK" if e["success"] else "—"
        labels.append(
            f'<label for="{rid}" class="rb-model-btn">'
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
            f"<div><dt>Simulación</dt><dd>{duration} s</dd></div>"
            f"<div><dt>Resultado</dt><dd>{badge}</dd></div>"
            f"</dl></div></div>"
        )

    blurb_html = f'<p class="rb-blurb">{blurb}</p>' if blurb else ""
    standalone_note = ""
    if standalone:
        standalone_note = (
            f'<p class="rb-blurb">Episodio determinista (semilla {RENDER_SEED}). '
            f"Elegí un botón para cambiar de modelo.</p>"
        )

    return f"""<style>
{chr(10).join(css_rules)}
</style>
<div class="rb-wrap" id="{player_id}">
  {standalone_note or blurb_html}
  {''.join(radios)}
  <p class="rb-controls-label">Modelos entrenados ({n}) · {duration}&nbsp;s</p>
  <div class="rb-btn-grid">
    {''.join(labels)}
  </div>
  <div class="rb-panels">
    {''.join(panels)}
  </div>
</div>
"""


def collect_entries(
    results: list[dict],
    args: argparse.Namespace,
    *,
    duration: int,
) -> list[dict]:
    html_entries: list[dict] = []
    out_videos = videos_dir(duration)

    for i, row in enumerate(results, 1):
        hidden = row["hidden"]
        timesteps = row["timesteps"]
        model_path = MODELS_DIR / f"ppo_H{hidden}_T{timesteps}.zip"
        video_name = f"H{hidden}_T{timesteps}.mp4"
        video_path = out_videos / video_name

        if not args.html_only:
            if not model_path.exists():
                print(f"[skip] modelo no encontrado: {model_path.name}")
                continue
            if args.skip_existing and video_path.exists():
                print(f"[skip] video existente ({duration}s): {video_name}")
            else:
                print(f"[{i}/{len(results)}] Grabando {duration}s → {video_name}…", flush=True)
                n_frames = record_episode(model_path, video_path, duration=duration)
                print(f"    → {n_frames} frames, {video_path.stat().st_size // 1024} KB")

        if not video_path.exists():
            print(f"[skip] video no encontrado ({duration}s): {video_name}")
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
                "video_file": f"videos/d{duration}/{video_name}",
            }
        )

    return html_entries


def main() -> None:
    args = parse_args()
    results = load_results()
    results.sort(key=lambda r: (r["hidden"], r["timesteps"]))

    for duration, player_id, embed_path, blurb in VIDEO_BLOCKS:
        base_entries = collect_entries(results, args, duration=duration)
        if not base_entries:
            raise SystemExit(f"No hay videos para embeber ({duration}s).")

        print(f"Codificando videos {duration}s en base64…")
        embed_entries = []
        for e in base_entries:
            video_path = OUT_DIR / e["video_file"]
            embed_entries.append({**e, "video": video_data_url(video_path)})

        embed_path.write_text(
            build_css_only_player(
                embed_entries,
                standalone=False,
                player_id=player_id,
                duration=duration,
                blurb=blurb,
            ),
            encoding="utf-8",
        )

        embed_kb = embed_path.stat().st_size // 1024
        print(f"  Embed {duration}s: {embed_path} ({embed_kb} KB, {len(base_entries)} videos)")


if __name__ == "__main__":
    main()
