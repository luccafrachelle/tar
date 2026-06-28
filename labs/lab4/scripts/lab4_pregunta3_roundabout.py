#!/usr/bin/env python3
"""
Lab 4 — Pregunta 3: barrido de arquitectura (H) y presupuesto (T) en roundabout-v0.

Entrena PPO con la configuración del enunciado, evalúa cada combinación y guarda
métricas + figuras en labs/lab4/results/pregunta3/.

Uso:
    python scripts/lab4_pregunta3_roundabout.py
    python scripts/lab4_pregunta3_roundabout.py --resume
    python scripts/lab4_pregunta3_roundabout.py --quick   # grid reducido (prueba)
"""

from __future__ import annotations

import argparse
import json
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import gymnasium as gym
import highway_env  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import DummyVecEnv

warnings.filterwarnings("ignore", category=DeprecationWarning)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "pregunta3"
MODELS_DIR = OUT_DIR / "models"

N_CPU = 2
N_EVAL = 15
EVAL_SEED_BASE = 2026
PPO_KWARGS = dict(
    policy="MlpPolicy",
    learning_rate=5e-4,
    n_steps=64 // N_CPU,
    n_epochs=10,
    batch_size=64,
    gamma=0.8,
    clip_range=0.2,
)

# Criterio operativo de “resuelve”: sobrevive, rinde bien y no es política pasiva.
SUCCESS_CRASH_RATE = 0.10
SUCCESS_MIN_LENGTH = 10.0
SUCCESS_MIN_REWARD = 9.5
FIG_DPI = 400


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resume", action="store_true", help="Saltear runs ya guardados.")
    p.add_argument(
        "--quick",
        action="store_true",
        help="Grid reducido H={16,64,256}, T={1000,10000} para pruebas rápidas.",
    )
    return p.parse_args()


def grid(quick: bool) -> tuple[list[int], list[int]]:
    if quick:
        return [16, 64, 256], [1_000, 10_000]
    return [16, 32, 64, 128, 256], [1_000, 5_000, 20_000, 50_000]


def evaluate_policy_detailed(model, n_episodes: int = N_EVAL) -> dict:
    env = gym.make("roundabout-v0")
    rewards, crash_flags, lengths = [], [], []

    for ep in range(n_episodes):
        obs, _ = env.reset(seed=EVAL_SEED_BASE + ep)
        total_reward = 0.0
        steps = 0
        terminated = truncated = False

        while not (terminated or truncated):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _ = env.step(action)
            total_reward += float(reward)
            steps += 1

        rewards.append(total_reward)
        crash_flags.append(bool(terminated))
        lengths.append(steps)

    env.close()
    rewards = np.asarray(rewards, dtype=float)
    crash_flags = np.asarray(crash_flags, dtype=float)
    lengths = np.asarray(lengths, dtype=float)

    return {
        "mean_reward": float(rewards.mean()),
        "std_reward": float(rewards.std(ddof=1) if len(rewards) > 1 else 0.0),
        "crash_rate": float(crash_flags.mean()),
        "mean_episode_length": float(lengths.mean()),
        "std_episode_length": float(lengths.std(ddof=1) if len(lengths) > 1 else 0.0),
        "success": bool(
            crash_flags.mean() <= SUCCESS_CRASH_RATE
            and lengths.mean() >= SUCCESS_MIN_LENGTH
            and rewards.mean() > SUCCESS_MIN_REWARD
        ),
    }


def evaluate_random_baseline(n_episodes: int = N_EVAL) -> dict:
    env = gym.make("roundabout-v0")
    rewards, crash_flags, lengths = [], [], []
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=EVAL_SEED_BASE + ep)
        total_reward = 0.0
        steps = 0
        terminated = truncated = False
        while not (terminated or truncated):
            obs, reward, terminated, truncated, _ = env.step(env.action_space.sample())
            total_reward += float(reward)
            steps += 1
        rewards.append(total_reward)
        crash_flags.append(bool(terminated))
        lengths.append(steps)
    env.close()
    return {
        "mean_reward": float(np.mean(rewards)),
        "crash_rate": float(np.mean(crash_flags)),
        "mean_episode_length": float(np.mean(lengths)),
    }


def train_and_eval(hidden: int, timesteps: int, seed: int = 0) -> dict:
    t0 = time.perf_counter()
    env = make_vec_env(
        "roundabout-v0",
        n_envs=N_CPU,
        vec_env_cls=DummyVecEnv,
    )
    model = PPO(
        env=env,
        verbose=0,
        seed=seed,
        policy_kwargs=dict(net_arch=dict(pi=[hidden, hidden], vf=[hidden, hidden])),
        **PPO_KWARGS,
    )
    model.learn(total_timesteps=timesteps)
    train_seconds = time.perf_counter() - t0

    metrics = evaluate_policy_detailed(model)
    metrics.update(
        {
            "hidden": hidden,
            "timesteps": timesteps,
            "train_seconds": round(train_seconds, 1),
            "arch": f"[{hidden},{hidden}]",
            "seed": seed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    model_path = MODELS_DIR / f"ppo_H{hidden}_T{timesteps}.zip"
    model.save(str(model_path.with_suffix("")))  # SB3 añade .zip
    metrics["model_path"] = str(model_path)

    env.close()
    return metrics


def load_results(path: Path) -> list[dict]:
    if path.exists():
        return json.loads(path.read_text())
    return []


def save_results(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))


def make_plots(df: pd.DataFrame, baseline: dict, out_dir: Path) -> None:
    sns.set_theme(style="whitegrid", context="notebook", palette="deep")
    mpl_rc = {"figure.dpi": FIG_DPI, "savefig.dpi": FIG_DPI}

    with plt.rc_context(mpl_rc):
        # Heatmap recompensa media
        pivot_r = df.pivot(index="hidden", columns="timesteps", values="mean_reward")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(
            pivot_r.sort_index(ascending=False),
            annot=True,
            fmt=".2f",
            cmap="YlGnBu",
            ax=ax,
            cbar_kws={"label": "Recompensa Media (Eval.)"},
        )
        ax.set_title("Recompensa Media vs Arquitectura y Presupuesto")
        ax.set_xlabel("Total Timesteps")
        ax.set_ylabel("Neuronas por Capa (H)")
        fig.tight_layout()
        fig.savefig(out_dir / "heatmap_mean_reward.png")
        plt.close(fig)

        # Heatmap tasa de choque
        pivot_c = df.pivot(index="hidden", columns="timesteps", values="crash_rate")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(
            pivot_c.sort_index(ascending=False),
            annot=True,
            fmt=".0%",
            cmap="YlOrRd_r",
            vmin=0,
            vmax=1,
            ax=ax,
            cbar_kws={"label": "Tasa de Choque"},
        )
        ax.set_title("Tasa de Choque vs Arquitectura y Presupuesto")
        ax.set_xlabel("Total Timesteps")
        ax.set_ylabel("Neuronas por Capa (H)")
        fig.tight_layout()
        fig.savefig(out_dir / "heatmap_crash_rate.png")
        plt.close(fig)

        # Curvas: recompensa vs T (una línea por H)
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
        for hidden, grp in df.groupby("hidden"):
            grp = grp.sort_values("timesteps")
            axes[0].plot(
                grp["timesteps"], grp["mean_reward"], marker="o", label=f"H={hidden}"
            )
            axes[1].plot(
                grp["timesteps"], grp["crash_rate"], marker="o", label=f"H={hidden}"
            )

        axes[0].axhline(
            baseline["mean_reward"],
            color="grey",
            ls="--",
            lw=1.2,
            label="Política Aleatoria",
        )
        axes[0].axhline(
            SUCCESS_MIN_REWARD,
            color="#b45309",
            ls=":",
            lw=1.4,
            label=f"Umbral de Éxito ({SUCCESS_MIN_REWARD})",
        )
        axes[0].set_xscale("log")
        axes[0].set_xlabel("Total Timesteps")
        axes[0].set_ylabel("Recompensa Media")
        axes[0].set_title("Recompensa vs Presupuesto de Entrenamiento")
        axes[0].legend(fontsize=8, ncol=2)

        axes[1].axhline(
            baseline["crash_rate"],
            color="grey",
            ls="--",
            lw=1.2,
            label="Política Aleatoria",
        )
        axes[1].axhline(
            SUCCESS_CRASH_RATE,
            color="#b45309",
            ls=":",
            lw=1.4,
            label=f"Umbral de Éxito ({SUCCESS_CRASH_RATE:.0%})",
        )
        axes[1].set_xscale("log")
        axes[1].set_xlabel("Total Timesteps")
        axes[1].set_ylabel("Tasa de Choque")
        axes[1].set_title("Choques vs Presupuesto de Entrenamiento")
        axes[1].legend(fontsize=8, ncol=2)

        fig.tight_layout()
        fig.savefig(out_dir / "curves_vs_timesteps.png")
        plt.close(fig)

        # Tiempo de entrenamiento
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for hidden, grp in df.groupby("hidden"):
            grp = grp.sort_values("timesteps")
            ax.plot(grp["timesteps"], grp["train_seconds"], marker="s", label=f"H={hidden}")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Total Timesteps")
        ax.set_ylabel("Tiempo de Entrenamiento (s)")
        ax.set_title("Costo Computacional por Configuración")
        ax.legend(fontsize=8, ncol=2)
        fig.tight_layout()
        fig.savefig(out_dir / "train_time.png")
        plt.close(fig)


def write_summary(df: pd.DataFrame, baseline: dict, out_dir: Path) -> dict:
    successful = df[df["success"]].copy()
    if successful.empty:
        best = df.sort_values(["crash_rate", "mean_reward"], ascending=[True, False]).iloc[0]
        best_label = "mejor aproximación (sin cumplir criterio estricto)"
    else:
        best = successful.sort_values(["hidden", "timesteps"]).iloc[0]
        best_label = "configuración mínima que resuelve (menor H y T con éxito)"

    summary = {
        "baseline_random": baseline,
        "success_criteria": {
            "max_crash_rate": SUCCESS_CRASH_RATE,
            "min_mean_episode_length": SUCCESS_MIN_LENGTH,
            "min_mean_reward": SUCCESS_MIN_REWARD,
        },
        "n_runs": int(len(df)),
        "n_successful": int(successful.shape[0]),
        "best_run": {
            "label": best_label,
            "hidden": int(best["hidden"]),
            "timesteps": int(best["timesteps"]),
            "arch": str(best["arch"]),
            "mean_reward": float(best["mean_reward"]),
            "crash_rate": float(best["crash_rate"]),
            "mean_episode_length": float(best["mean_episode_length"]),
            "train_seconds": float(best["train_seconds"]),
            "success": bool(best["success"]),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    lines = [
        "# Resumen Pregunta 3 — roundabout-v0\n",
        f"- Baseline aleatorio: recompensa media {baseline['mean_reward']:.2f}, "
        f"choque {baseline['crash_rate']:.0%}, "
        f"longitud media {baseline['mean_episode_length']:.1f} pasos.\n",
        f"- Criterio de éxito: choque ≤ {SUCCESS_CRASH_RATE:.0%}, "
        f"longitud media ≥ {SUCCESS_MIN_LENGTH:.0f} pasos y "
        f"recompensa media > {SUCCESS_MIN_REWARD}.\n",
        f"- Runs exitosos: {successful.shape[0]} / {len(df)}.\n",
        f"- {best_label}: H={int(best['hidden'])}, T={int(best['timesteps'])}, "
        f"recompensa={best['mean_reward']:.2f}, choque={best['crash_rate']:.0%}, "
        f"entrenamiento={best['train_seconds']:.0f}s.\n",
    ]
    (out_dir / "summary.md").write_text("".join(lines))
    return summary


def main() -> None:
    args = parse_args()
    hidden_sizes, timesteps_list = grid(args.quick)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    results_path = OUT_DIR / "results.json"
    rows = load_results(results_path)
    done_keys = {(r["hidden"], r["timesteps"]) for r in rows}

    print("Evaluando baseline aleatorio…")
    baseline = evaluate_random_baseline()
    (OUT_DIR / "baseline_random.json").write_text(json.dumps(baseline, indent=2))

    total = len(hidden_sizes) * len(timesteps_list)
    run_idx = len(done_keys)

    for hidden in hidden_sizes:
        for timesteps in timesteps_list:
            key = (hidden, timesteps)
            if args.resume and key in done_keys:
                print(f"[skip] H={hidden}, T={timesteps}")
                continue

            run_idx += 1 if key not in done_keys else 0
            print(f"[{run_idx}/{total}] Entrenando H={hidden}, T={timesteps}…", flush=True)
            row = train_and_eval(hidden, timesteps)
            rows.append(row)
            save_results(results_path, rows)
            print(
                f"    → reward={row['mean_reward']:.2f}, crash={row['crash_rate']:.0%}, "
                f"len={row['mean_episode_length']:.1f}, t={row['train_seconds']:.0f}s, "
                f"success={row['success']}",
                flush=True,
            )

    df = pd.DataFrame(rows).sort_values(["hidden", "timesteps"])
    df.to_csv(OUT_DIR / "results.csv", index=False)

    make_plots(df, baseline, OUT_DIR)
    summary = write_summary(df, baseline, OUT_DIR)

    print("\nListo.")
    print(f"Resultados: {OUT_DIR}")
    print(f"Mejor run: {summary['best_run']}")


if __name__ == "__main__":
    main()
