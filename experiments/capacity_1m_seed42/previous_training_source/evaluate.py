"""Frozen, paired-seed evaluations. No gradient updates or replay writes."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import torch

from agents import ActorCritic, load_model
from env import DoodleEnv


def evaluate_policy(model, *, mode="original", observation="full", seeds=range(10000, 10020),
                    stochastic=False, max_steps=1500, trace_seed=None):
    env = DoodleEnv(mode=mode, observation=observation, max_steps=max_steps)
    episodes = []
    trace = []
    rng = np.random.default_rng(9181)
    with torch.inference_mode():
        for seed in seeds:
            obs = env.reset(seed=int(seed))
            if isinstance(obs, tuple):
                obs = obs[0]
            terminated = truncated = False
            while not (terminated or truncated):
                inp = torch.from_numpy(np.asarray(obs, dtype=np.float32)).unsqueeze(0)
                if isinstance(model, ActorCritic):
                    logits, _ = model(inp)
                    if stochastic:
                        probs = torch.softmax(logits, -1)[0].numpy().astype(np.float64)
                        action = int(rng.choice(3, p=probs / probs.sum()))
                    else:
                        action = int(logits.argmax(-1)[0])
                else:
                    action = int(model(inp).argmax(-1)[0])
                obs, reward, terminated, truncated, info = env.step(action)
                if trace_seed is not None and int(seed) == trace_seed:
                    trace.append({"action": action, "reward": float(reward), "info": _native(info)})
            episodes.append({"seed": int(seed), **{key: _native(info.get(key)) for key in
                ("score", "height", "landings", "springs", "fragile_used", "death_reason", "steps", "frames", "episode_return")},
                "terminated": bool(terminated), "truncated": bool(truncated)})
    result = {"mode": mode, "observation": observation, "stochastic": stochastic,
              "episode_count": len(episodes), "episodes": episodes, "summary": summarize(episodes)}
    if trace_seed is not None:
        result["trace_seed"], result["trace"] = trace_seed, trace
    return result


def _native(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {k: _native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_native(v) for v in value]
    return value


def summarize(episodes):
    heights = np.array([r["height"] for r in episodes], np.float64)
    reasons = {}
    for ep in episodes:
        key = ep["death_reason"] or ("time_limit" if ep["truncated"] else "unknown")
        reasons[key] = reasons.get(key, 0) + 1
    return {"mean_score": float(np.mean([r["score"] for r in episodes])), "median_score": float(np.median([r["score"] for r in episodes])), "mean_height": float(heights.mean()), "median_height": float(np.median(heights)),
            "height_sd": float(heights.std(ddof=1)) if len(heights) > 1 else 0.,
            "p10_height": float(np.percentile(heights, 10)), "p90_height": float(np.percentile(heights, 90)),
            "mean_return": float(np.mean([r["episode_return"] for r in episodes])),
            "mean_steps": float(np.mean([r["steps"] for r in episodes])),
            "mean_frames": float(np.mean([r["frames"] for r in episodes])),
            "mean_landings": float(np.mean([r["landings"] for r in episodes])),
            "threshold_rates": {str(h): float(np.mean(heights >= h)) for h in (1000, 3000, 6000)},
            "time_limit_rate": float(np.mean([r["truncated"] for r in episodes])), "death_counts": reasons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--mode", choices=("original", "viewport600", "viewport900"), default="original")
    parser.add_argument("--seed-start", type=int, default=20000)
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--max-steps", type=int, default=1500)
    parser.add_argument("--output", required=True)
    parser.add_argument("--trace-seed", type=int)
    args = parser.parse_args()
    torch.set_num_threads(1)
    model, record = load_model(args.checkpoint)
    results = evaluate_policy(model, mode=args.mode, observation=record["observation"],
                seeds=range(args.seed_start, args.seed_start + args.episodes), stochastic=args.stochastic,
                max_steps=args.max_steps, trace_seed=args.trace_seed)
    results.update({"algorithm": record["algorithm"], "training_seed": record["seed"],
                    "training_steps": record["steps"], "checkpoint": str(args.checkpoint),
                    "policy_frozen": True, "selection": "sample" if args.stochastic else "argmax"})
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: results[k] for k in ("algorithm", "training_seed", "mode", "summary")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
