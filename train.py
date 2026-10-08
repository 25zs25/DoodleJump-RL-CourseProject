"""Reproducible DQN, Double DQN, PPO training with exact env.step budgets.

Each env.step consists of four physical simulation frames (or fewer if dead).
Validation seeds are held out from training; final test seeds are never read.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import time
from collections import deque
import numpy as np
import torch

from agents import (ActorCritic, QNetwork, ReplayBuffer, dqn_update, export_model,
                    generalized_advantages, ppo_update, seed_everything)
from evaluate import evaluate_policy, _native
from env import DoodleEnv
from viewport import load_viewport

ROOT = Path(__file__).resolve().parent


class Recorder:
    def __init__(self, args, dim):
        self.args = args
        self.folder = ROOT / "models" / args.run_id
        self.folder.mkdir(parents=True, exist_ok=False)
        self.started = time.perf_counter()
        self.frames = 0
        self.curve = []
        self.episodes = []
        self.recent = deque(maxlen=100)
        self.best_score = -float("inf")
        self.dim = dim
        self.config = {**vars(args), "observation_dim": dim, "hidden": args.hidden,
            "compute": {"device": args.device, "gpu": torch.cuda.get_device_name(0) if args.device == "cuda" else None,
                        "torch_threads": torch.get_num_threads(), "precision": "float32",
                        "cuda_matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32},
            "training_map_seed_start": 1000000 + args.seed * 10000,
            "validation_seeds": list(range(10000, 10020)), "mode": "original",
            "viewport": [args.viewport_width,args.viewport_height], "native_window": args.native_geometry,
            "environment_version": "native-viewport-v2",
            "versions": {"python": platform.python_version(), "torch": str(torch.__version__), "numpy": np.__version__},
            "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                              for name in ("agents.py", "env.py", "train.py", "evaluate.py", "viewport.py")}}
        self.config["hyperparameters"] = ({"gamma": .99, "learning_rate": args.learning_rate or .0005,
            "buffer": 100000, "learning_starts": 2500, "batch_size": 128, "train_every": 4,
            "target_every": 2000, "epsilon_start": 1., "epsilon_end": .05,
            "epsilon_decay_steps": args.epsilon_decay_steps, "loss": "Huber", "max_grad_norm": 10.}
            if args.algorithm != "ppo" else {"gamma": .99, "gae_lambda": .95,
            "learning_rate": args.learning_rate or .0003, "vector_envs": 8, "rollout_length": 128,
            "epochs": 4, "minibatch": 256, "clip": .2, "entropy_coef": .01,
            "value_coef": .5, "max_grad_norm": .5, "advantage_normalization": True,
            "value_clip": True})
        self.write("config.json", self.config)

    def write(self, filename, value):
        (self.folder / filename).write_text(json.dumps(_native(value), ensure_ascii=False, indent=2), encoding="utf-8")

    def episode(self, steps, info, terminated, truncated):
        item = {"training_step": steps, **{key: _native(info.get(key)) for key in
            ("score", "height", "landings", "springs", "fragile_used", "death_reason", "steps", "frames", "episode_return")},
            "terminated": bool(terminated), "truncated": bool(truncated)}
        self.episodes.append(item)
        self.recent.append(item)

    def checkpoint(self, model, optimizer, steps, metrics, *, final=False):
        evaluated = evaluate_policy(model, observation=self.args.obs, seeds=range(10000, 10020),
                                    height=self.args.viewport_height, width=self.args.viewport_width)
        score = evaluated["summary"]["mean_score"]
        seconds = time.perf_counter() - self.started
        point = {"steps": steps, "frames": self.frames, "seconds": seconds,
                 "interactions_per_second": steps / max(seconds, 1e-9),
                 "train_episodes": len(self.episodes), "validation": evaluated["summary"], **_native(metrics)}
        if self.recent:
            point["recent_train_mean_height"] = float(np.mean([r["height"] for r in self.recent]))
            point["recent_train_mean_return"] = float(np.mean([r["episode_return"] for r in self.recent]))
        self.curve.append(point)
        metadata = {"algorithm": self.args.algorithm, "seed": self.args.seed, "steps": steps,
                    "frames": self.frames, "observation": self.args.obs, "observation_dim": self.dim, "hidden": self.args.hidden,
                    "device": self.args.device,
                    "viewport": [self.args.viewport_width,self.args.viewport_height],
                    "environment_version": "native-viewport-v2",
                    "run_id": self.args.run_id}
        record = {**metadata, "state_dict": model.state_dict(), "optimizer": optimizer.state_dict()}
        name = "final" if final else f"step_{steps}"
        torch.save(record, self.folder / f"{name}.pt")
        export_model(model, self.folder / f"{name}.json", {**metadata, "id": self.args.run_id})
        if score > self.best_score:
            self.best_score = score
            torch.save(record, self.folder / "best.pt")
            export_model(model, self.folder / "best.json", {**metadata, "id": self.args.run_id})
            self.write("best_validation.json", {"steps": steps, **evaluated})
        self.write("curve.json", self.curve)
        self.write("episodes.json", self.episodes)
        self.write("status.json", {**metadata, "training_complete": final, "elapsed_seconds": seconds,
                                    "best_validation_score": self.best_score,
                                    "parameters": sum(p.numel() for p in model.parameters()),
                                    "gradient_updates": metrics.get("gradient_updates"),
                                    "config": self.config})
        print(json.dumps({"run": self.args.run_id, "steps": steps, "score": round(score, 2),
                          "recent_train_height": round(point.get("recent_train_mean_height", 0), 2),
                          "seconds": round(seconds, 2), "final": final}), flush=True)


def reset(env, seed):
    result = env.reset(seed=seed)
    return result[0] if isinstance(result, tuple) else result


def train_dqn(args):
    rng = np.random.default_rng(args.seed)
    env = DoodleEnv(mode="original", observation=args.obs, height=args.viewport_height, width=args.viewport_width)
    seedbase = 1000000 + args.seed * 10000
    episode = 0
    obs = reset(env, seedbase)
    previous_frames = 0
    model = QNetwork(len(obs), args.hidden).to(args.device)
    target = QNetwork(len(obs), args.hidden).to(args.device)
    target.load_state_dict(model.state_dict())
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate or .0005)
    replay = ReplayBuffer(100000, len(obs), args.seed)
    recorder = Recorder(args, len(obs))
    gradient_updates = 0
    recent_metrics = {}
    next_checkpoint = args.checkpoint_every
    for step in range(1, args.steps + 1):
        epsilon = max(.05, 1 - .95 * step / max(1, args.epsilon_decay_steps))
        if rng.random() < epsilon:
            action = int(rng.integers(3))
        else:
            with torch.inference_mode():
                action = int(model(torch.from_numpy(np.asarray(obs, np.float32)).to(args.device)).argmax().item())
        next_obs, reward, terminated, truncated, info = env.step(action)
        # next_obs here is the final state, before resetting a time-limit episode.
        replay.add(obs, action, reward, next_obs, terminated)
        obs = next_obs
        recorder.frames += int(info["frames"]) - previous_frames
        previous_frames = int(info["frames"])
        if terminated or truncated:
            recorder.episode(step, info, terminated, truncated)
            episode += 1
            obs = reset(env, seedbase + episode)
            previous_frames = 0
        if step >= 2500 and step % 4 == 0:
            batch = tuple(tensor.to(args.device) for tensor in replay.sample(128))
            recent_metrics = dqn_update(model, target, optimizer, batch, .99,
                                       args.algorithm == "double_dqn")
            gradient_updates += 1
        if step % 2000 == 0:
            target.load_state_dict(model.state_dict())
        if step >= next_checkpoint or step == args.steps:
            recorder.checkpoint(model, optimizer, step, {**recent_metrics, "epsilon": epsilon,
                                "gradient_updates": gradient_updates}, final=step == args.steps)
            next_checkpoint += args.checkpoint_every


def train_ppo(args):
    rng = np.random.default_rng(args.seed)
    nenv = 8
    seedbase = 1000000 + args.seed * 10000
    envs = [DoodleEnv(mode="original", observation=args.obs, height=args.viewport_height, width=args.viewport_width) for _ in range(nenv)]
    episodes = np.zeros(nenv, np.int64)
    observations = [reset(env, seedbase + i * 100000) for i, env in enumerate(envs)]
    previous_frames = [0] * nenv
    model = ActorCritic(len(observations[0]), args.hidden).to(args.device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate or .0003, eps=1e-5)
    recorder = Recorder(args, len(observations[0]))
    steps = 0
    next_checkpoint = args.checkpoint_every
    gradient_updates = 0
    while steps < args.steps:
        # Per-env lists permit an exact final budget even when not divisible by 8.
        storage = [[] for _ in range(nenv)]
        for _ in range(128):
            active = min(nenv, args.steps - steps)
            if active == 0:
                break
            tensor = torch.from_numpy(np.asarray(observations[:active], dtype=np.float32)).to(args.device)
            with torch.no_grad():
                actions, logp, _, values = model.action_value(tensor)
            for i in range(active):
                next_obs, reward, terminated, truncated, info = envs[i].step(int(actions[i]))
                with torch.no_grad():
                    _, next_value = model(torch.from_numpy(np.asarray(next_obs, np.float32)).unsqueeze(0).to(args.device))
                storage[i].append((observations[i].copy(), int(actions[i]), float(logp[i]), float(values[i]),
                                  float(reward), float(next_value[0]), float(terminated), float(terminated or truncated)))
                steps += 1
                recorder.frames += int(info["frames"]) - previous_frames[i]
                previous_frames[i] = int(info["frames"])
                observations[i] = next_obs
                if terminated or truncated:
                    recorder.episode(steps, info, terminated, truncated)
                    episodes[i] += 1
                    observations[i] = reset(envs[i], seedbase + i * 100000 + int(episodes[i]))
                    previous_frames[i] = 0
        columns = [[] for _ in range(6)]
        for stream in storage:
            if not stream:
                continue
            obs, act, logp, val, rew, nxt, term, end = zip(*stream)
            advantage, returns = generalized_advantages(*[torch.tensor(x, dtype=torch.float32) for x in
                (rew, val, nxt, term, end)], .99, .95)
            tensors = [torch.from_numpy(np.asarray(obs, np.float32)), torch.tensor(act),
                       torch.tensor(logp), torch.tensor(val), advantage, returns]
            for target_col, value in zip(columns, tensors):
                target_col.append(value)
        rollout = [torch.cat(column).to(args.device) for column in columns]
        metrics = ppo_update(model, optimizer, rollout, rng=rng)
        gradient_updates += 4 * int(np.ceil(len(rollout[0]) / 256))
        if steps >= next_checkpoint or steps == args.steps:
            recorder.checkpoint(model, optimizer, steps, {**metrics, "gradient_updates": gradient_updates},
                                final=steps == args.steps)
            while next_checkpoint <= steps:
                next_checkpoint += args.checkpoint_every


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algorithm", required=True, choices=("dqn", "double_dqn", "ppo"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=1000000)
    parser.add_argument("--obs", choices=("full", "no_velocity"), default="full")
    parser.add_argument("--hidden", type=int, default=128)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--viewport-json", required=True, help="Export fresh native geometry from the preview; no implicit 720-height training")
    parser.add_argument("--run-id")
    parser.add_argument("--learning-rate", type=float)
    parser.add_argument("--epsilon-decay-steps", type=int,
                        help="DQN exploration annealing duration (default 60%% of step budget)")
    parser.add_argument("--checkpoint-every", type=int, default=50000)
    args = parser.parse_args()
    try:
        args.native_geometry = load_viewport(args.viewport_json)
    except (ValueError,OSError) as exc:
        parser.error(str(exc))
    args.viewport_width,args.viewport_height = args.native_geometry['width'],args.native_geometry['height']
    if args.steps <= 0 or args.checkpoint_every <= 0 or args.hidden <= 0:
        parser.error("steps, checkpoint-every and hidden must be positive")
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA was requested but is not available")
    args.run_id = args.run_id or f"{args.algorithm}_{args.obs}_h{args.hidden}_{args.device}_v{args.viewport_height:g}_w{args.viewport_width:g}_seed{args.seed}_{args.steps}"
    args.epsilon_decay_steps = args.epsilon_decay_steps or int(args.steps * .6)
    seed_everything(args.seed)
    (train_ppo if args.algorithm == "ppo" else train_dqn)(args)


if __name__ == "__main__":
    main()
