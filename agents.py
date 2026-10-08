"""Small, explicit PyTorch agents for the Doodle Jump experiments.

DQN and Double DQN differ only in the next-action selection in the TD target.
PPO uses an identical two-layer policy backbone and a separate value head.
No teacher, trajectory planner, or scripted policy is used in training.
"""
from __future__ import annotations

import json
from pathlib import Path
import random
import numpy as np
import torch
from torch import nn
from torch.distributions import Categorical


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)


class QNetwork(nn.Module):
    def __init__(self, observation_dim: int, hidden: int = 128):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(observation_dim, hidden), nn.ReLU(),
                                 nn.Linear(hidden, hidden), nn.ReLU(),
                                 nn.Linear(hidden, 3))

    def forward(self, x):
        return self.net(x)


class ActorCritic(nn.Module):
    def __init__(self, observation_dim: int, hidden: int = 128):
        super().__init__()
        self.trunk = nn.Sequential(nn.Linear(observation_dim, hidden), nn.ReLU(),
                                   nn.Linear(hidden, hidden), nn.ReLU())
        self.policy = nn.Linear(hidden, 3)
        self.value = nn.Linear(hidden, 1)
        for layer in self.modules():
            if isinstance(layer, nn.Linear):
                nn.init.orthogonal_(layer.weight, np.sqrt(2))
                nn.init.zeros_(layer.bias)
        nn.init.orthogonal_(self.policy.weight, .01)
        nn.init.orthogonal_(self.value.weight, 1.)

    def forward(self, x):
        hidden = self.trunk(x)
        return self.policy(hidden), self.value(hidden).squeeze(-1)

    def action_value(self, observations, actions=None):
        logits, value = self(observations)
        dist = Categorical(logits=logits)
        if actions is None:
            actions = dist.sample()
        return actions, dist.log_prob(actions), dist.entropy(), value


class ReplayBuffer:
    def __init__(self, size: int, observation_dim: int, seed: int):
        self.obs = np.empty((size, observation_dim), np.float32)
        self.next_obs = np.empty_like(self.obs)
        self.action = np.empty(size, np.int64)
        self.reward = np.empty(size, np.float32)
        # A time limit truncates the rollout but does not terminate the MDP.
        self.terminated = np.empty(size, np.float32)
        self.index = 0
        self.count = 0
        self.size = size
        self.rng = np.random.default_rng(seed)

    def add(self, obs, action, reward, next_obs, terminated):
        i = self.index
        self.obs[i], self.action[i], self.reward[i] = obs, action, reward
        self.next_obs[i], self.terminated[i] = next_obs, terminated
        self.index = (i + 1) % self.size
        self.count = min(self.count + 1, self.size)

    def sample(self, batch: int):
        indexes = self.rng.integers(0, self.count, batch)
        return tuple(torch.from_numpy(array[indexes]) for array in
                     (self.obs, self.action, self.reward, self.next_obs, self.terminated))


def dqn_update(network, target_network, optimizer, batch, gamma: float,
               double: bool, max_grad_norm: float = 10.):
    obs, actions, rewards, next_obs, terminated = batch
    with torch.no_grad():
        target_q = target_network(next_obs)
        if double:
            next_actions = network(next_obs).argmax(1, keepdim=True)
            next_values = target_q.gather(1, next_actions).squeeze(1)
        else:
            next_values = target_q.max(1).values
        targets = rewards + gamma * (1 - terminated) * next_values
    q = network(obs).gather(1, actions[:, None]).squeeze(1)
    loss = nn.functional.smooth_l1_loss(q, targets)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    norm = nn.utils.clip_grad_norm_(network.parameters(), max_grad_norm)
    optimizer.step()
    return {"loss": float(loss.detach()), "q_mean": float(q.detach().mean()),
            "target_mean": float(targets.mean()), "grad_norm": float(norm)}


def generalized_advantages(rewards, values, next_values, terminated, episode_ends,
                           gamma: float, gae_lambda: float):
    """GAE: bootstrap time limits; never pass advantage across a reset.

    next_values must be computed from the *final* next observation, not an
    auto-reset observation. `terminated` masks TD bootstrap; `episode_ends`
    (terminated OR truncated) masks recursion across independent episodes.
    """
    advantages = torch.zeros_like(rewards)
    last = torch.zeros_like(rewards[0])
    for t in reversed(range(len(rewards))):
        delta = rewards[t] + gamma * (1 - terminated[t]) * next_values[t] - values[t]
        last = delta + gamma * gae_lambda * (1 - episode_ends[t]) * last
        advantages[t] = last
    return advantages, advantages + values


def ppo_update(network, optimizer, rollout, *, epochs=4, minibatch=256,
               clip=.2, entropy_coef=.01, value_coef=.5, max_grad_norm=.5,
               rng=None):
    observations, actions, old_logp, old_values, advantages, returns = rollout
    advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-8)
    indexes = np.arange(len(observations))
    records = []
    for _ in range(epochs):
        rng.shuffle(indexes)
        for start in range(0, len(indexes), minibatch):
            idx = indexes[start:start + minibatch]
            _, logp, entropy, value = network.action_value(observations[idx], actions[idx])
            ratio = (logp - old_logp[idx]).exp()
            loss_policy = -torch.minimum(ratio * advantages[idx],
                                        ratio.clamp(1 - clip, 1 + clip) * advantages[idx]).mean()
            # Value clipping against the rollout value is used consistently.
            clipped_value = old_values[idx] + (value - old_values[idx]).clamp(-clip, clip)
            loss_value = .5 * torch.maximum((value - returns[idx]).square(),
                                             (clipped_value - returns[idx]).square()).mean()
            loss = loss_policy + value_coef * loss_value - entropy_coef * entropy.mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(network.parameters(), max_grad_norm)
            optimizer.step()
            with torch.no_grad():
                logratio = logp - old_logp[idx]
                approx_kl = ((ratio - 1) - logratio).mean()
                records.append((float(loss_policy), float(loss_value), float(entropy.mean()),
                                float(approx_kl), float((abs(ratio - 1) > clip).float().mean())))
    means = np.mean(records, axis=0)
    return dict(zip(("policy_loss", "value_loss", "entropy", "approx_kl", "clip_fraction"), means.tolist()))


def load_model(path):
    record = torch.load(path, map_location="cpu", weights_only=True)
    cls = ActorCritic if record["algorithm"] == "ppo" else QNetwork
    model = cls(record["observation_dim"], record.get("hidden", 128))
    model.load_state_dict(record["state_dict"])
    model.eval()
    return model, record


def export_model(model, path, metadata):
    linear = ([model.trunk[0], model.trunk[2], model.policy] if isinstance(model, ActorCritic)
              else [model.net[0], model.net[2], model.net[4]])
    layers = [{"weights": layer.weight.detach().cpu().tolist(),
               "bias": layer.bias.detach().cpu().tolist(),
               "activation": "relu" if i < 2 else "linear"} for i, layer in enumerate(linear)]
    record = {**metadata, "dimensions": [linear[0].in_features, *[layer.out_features for layer in linear]],
              "action_names": ["left", "stay", "right"], "selection": "argmax", "layers": layers}
    Path(path).write_text(json.dumps(record, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
