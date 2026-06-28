#!/usr/bin/env python3
"""
Genera tablas HTML con selector CSS para Lab4 Pregunta 3:
  - Resultados del barrido
  - Comparación vs. política aleatoria (solo diferencias)

Salida: labs/lab4/results/pregunta3/results_tables_embed.html
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "pregunta3"
RESULTS_CSV = OUT_DIR / "results.csv"
BASELINE_JSON = OUT_DIR / "baseline_random.json"
EMBED_PATH = OUT_DIR / "results_tables_embed.html"

SUCCESS_CRASH_RATE = 0.10
SUCCESS_MIN_LENGTH = 10.0
SUCCESS_MIN_REWARD = 9.5


def fmt_timesteps(t: int) -> str:
    return f"{t:,}".replace(",", "\u202f")


def fmt_reward(x: float) -> str:
    return f"{x:.2f}"


def fmt_pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def fmt_len(x: float) -> str:
    return f"{x:.1f}"


def fmt_time(x: float) -> str:
    return str(int(round(x)))


def fmt_delta(d: float, *, decimals: int = 2, suffix: str = "") -> str:
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.{decimals}f}{suffix}"


def delta_class(d: float, *, higher_is_better: bool) -> str:
    good = d > 0 if higher_is_better else d < 0
    if abs(d) < 1e-9:
        return "p3-delta-neutral"
    return "p3-delta-good" if good else "p3-delta-bad"


def is_success(row: pd.Series, baseline: dict) -> bool:
    """Evita contar como éxito una política que solo sobrevive sin rendimiento real."""
    return bool(
        row["crash_rate"] <= SUCCESS_CRASH_RATE
        and row["mean_episode_length"] >= SUCCESS_MIN_LENGTH
        and row["mean_reward"] > SUCCESS_MIN_REWARD
    )


def beats_random(row: pd.Series, baseline: dict) -> bool:
    dr = row["mean_reward"] - baseline["mean_reward"]
    dc = baseline["crash_rate"] - row["crash_rate"]
    dl = row["mean_episode_length"] - baseline["mean_episode_length"]
    return dr > 0 and dc > 0 and dl > 0


def build_main_table(df: pd.DataFrame, baseline: dict) -> str:
    rows = []
    for _, r in df.iterrows():
        ok = "<strong>sí</strong>" if is_success(r, baseline) else "no"
        rows.append(
            "<tr>"
            f"<td>{int(r['hidden'])}</td>"
            f"<td>{fmt_timesteps(int(r['timesteps']))}</td>"
            f"<td>{fmt_reward(r['mean_reward'])}</td>"
            f"<td>{fmt_pct(r['crash_rate'])}</td>"
            f"<td>{fmt_len(r['mean_episode_length'])}</td>"
            f"<td>{fmt_time(r['train_seconds'])}</td>"
            f"<td>{ok}</td>"
            "</tr>"
        )
    return (
        '<table class="p3-tbl">'
        "<thead><tr>"
        "<th><em>H</em></th><th><em>T</em></th>"
        "<th>Recompensa</th><th>Choque</th><th>Longitud</th>"
        "<th>Tiempo (s)</th><th>¿Resuelve?</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def build_compare_table(df: pd.DataFrame, baseline: dict) -> str:
    br = baseline["mean_reward"]
    bc = baseline["crash_rate"]
    bl = baseline["mean_episode_length"]

    baseline_row = (
        "<tr class='p3-baseline-row'>"
        "<td colspan='2'><strong>Aleatoria</strong></td>"
        "<td>0.00</td>"
        "<td>0 pp</td>"
        "<td>0.0</td>"
        "<td>referencia</td>"
        "</tr>"
    )

    rows = [baseline_row]
    for _, r in df.iterrows():
        dr = r["mean_reward"] - br
        dc_pp = 100 * (bc - r["crash_rate"])
        dl = r["mean_episode_length"] - bl
        better = "<strong>sí</strong>" if beats_random(r, baseline) else "no"
        rows.append(
            "<tr>"
            f"<td>{int(r['hidden'])}</td>"
            f"<td>{fmt_timesteps(int(r['timesteps']))}</td>"
            f"<td class='{delta_class(dr, higher_is_better=True)}'>{fmt_delta(dr)}</td>"
            f"<td class='{delta_class(dc_pp, higher_is_better=True)}'>{fmt_delta(dc_pp, decimals=0, suffix=' pp')}</td>"
            f"<td class='{delta_class(dl, higher_is_better=True)}'>{fmt_delta(dl, decimals=1)}</td>"
            f"<td>{better}</td>"
            "</tr>"
        )

    return (
        '<p class="p3-tbl-note">'
        f"Referencia aleatoria: recompensa {fmt_reward(br)}, choque {fmt_pct(bc)}, "
        f"longitud {fmt_len(bl)} pasos. "
        "Solo diferencias PPO − aleatoria (choque en puntos porcentuales; "
        "positivo = menos choques). "
        f"¿Supera aleatoria? = las tres Δ son estrictamente positivas.</p>"
        '<table class="p3-tbl p3-tbl-cmp">'
        "<thead><tr>"
        "<th><em>H</em></th><th><em>T</em></th>"
        "<th>Δ Recompensa</th><th>Δ Choque</th><th>Δ Longitud</th>"
        "<th>¿Supera aleatoria?</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def build_embed_html(df: pd.DataFrame, baseline: dict) -> str:
    css = """
.p3-tbl-wrap { margin: .75rem 0 1.25rem; max-width: 100%; }
.p3-tbl-wrap .p3-tbl-input { position: absolute; opacity: 0; width: 0; height: 0; pointer-events: none; }
.p3-tbl-wrap .p3-tbl-panel { display: none; overflow-x: auto; }
.p3-tbl-wrap .p3-tbl-tabs {
  display: flex; gap: .45rem; margin-bottom: .65rem; flex-wrap: wrap;
}
.p3-tbl-wrap .p3-tbl-tab {
  display: inline-block; border: 1px solid var(--bs-border-color, #dde3ea);
  background: var(--bs-body-bg, #fff); color: inherit; border-radius: 8px;
  padding: .4rem .85rem; font-size: .88rem; font-weight: 600; cursor: pointer;
  transition: border-color .15s, background .15s, box-shadow .15s;
}
.p3-tbl-wrap .p3-tbl-tab:hover { border-color: #2563eb; background: #dbeafe; }
#p3-tbl-main:checked ~ .p3-tbl-tabs label[for='p3-tbl-main'],
#p3-tbl-cmp:checked ~ .p3-tbl-tabs label[for='p3-tbl-cmp'] {
  border-color: #2563eb; background: #dbeafe;
  box-shadow: 0 0 0 2px rgba(37,99,235,.22);
}
#p3-tbl-main:checked ~ .p3-tbl-panels .p3-tbl-panel-main { display: block; }
#p3-tbl-cmp:checked ~ .p3-tbl-panels .p3-tbl-panel-cmp { display: block; }
.p3-tbl {
  width: 100%; border-collapse: collapse; font-size: .88rem;
  margin: 0; line-height: 1.35;
}
.p3-tbl th, .p3-tbl td {
  border: 1px solid var(--bs-border-color, #dde3ea);
  padding: .38rem .5rem; text-align: center; vertical-align: middle;
}
.p3-tbl thead th { background: var(--bs-tertiary-bg, #f3f5f7); font-weight: 650; }
.p3-tbl tbody tr:nth-child(even) { background: rgba(0,0,0,.02); }
.p3-baseline-row { background: #fff7ed !important; font-style: normal; }
.p3-tbl-note {
  font-size: .82rem; color: var(--bs-secondary-color, #5c6570);
  margin: 0 0 .55rem; line-height: 1.45;
}
.p3-delta-good { color: #15803d; font-weight: 600; }
.p3-delta-bad { color: #b91c1c; font-weight: 600; }
.p3-delta-neutral { color: inherit; }
"""

    main_table = build_main_table(df, baseline)
    cmp_table = build_compare_table(df, baseline)

    return f"""<style>
{css}
</style>
<div class="p3-tbl-wrap">
  <input type="radio" name="p3-tbl-view" id="p3-tbl-main" class="p3-tbl-input" checked>
  <input type="radio" name="p3-tbl-view" id="p3-tbl-cmp" class="p3-tbl-input">
  <div class="p3-tbl-tabs">
    <label for="p3-tbl-main" class="p3-tbl-tab">Resultados del barrido</label>
    <label for="p3-tbl-cmp" class="p3-tbl-tab">Comparación vs. aleatoria</label>
  </div>
  <div class="p3-tbl-panels">
    <div class="p3-tbl-panel p3-tbl-panel-main">{main_table}</div>
    <div class="p3-tbl-panel p3-tbl-panel-cmp">{cmp_table}</div>
  </div>
</div>
"""


def main() -> None:
    df = pd.read_csv(RESULTS_CSV).sort_values(["hidden", "timesteps"])
    baseline = json.loads(BASELINE_JSON.read_text())
    EMBED_PATH.write_text(build_embed_html(df, baseline), encoding="utf-8")
    n_ok = sum(is_success(r, baseline) for _, r in df.iterrows())
    print(f"Tablas: {EMBED_PATH} ({n_ok}/20 resuelven con criterio actualizado)")


if __name__ == "__main__":
    main()
