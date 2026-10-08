"""Numerical algorithm checks against independently specified target values."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
import numpy as np
import torch
from torch import nn
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agents import QNetwork, export_model, generalized_advantages, dqn_update
torch.set_num_threads(1)

class ConstantQ(nn.Module):
    def __init__(self,values):
        super().__init__()
        self.values=nn.Parameter(torch.tensor(values,dtype=torch.float32))
    def forward(self,x):
        return self.values.expand(len(x),-1)

class AlgorithmTests(unittest.TestCase):
    def test_dqn_and_double_dqn_disagree_on_noisy_maximum(self):
        # Online chooses action1; target maximum lies at action0.
        # DQN: 3+0.9*10=12. DDQN: 3+0.9*2=4.8.
        for double,expected in [(False,12.),(True,4.8)]:
            online=ConstantQ([1.,5.,2.]);target=ConstantQ([10.,2.,0.])
            batch=(torch.zeros(1,209),torch.tensor([0]),torch.tensor([3.]),torch.zeros(1,209),torch.tensor([0.]))
            metrics=dqn_update(online,target,torch.optim.SGD(online.parameters(),lr=0),batch,.9,double)
            self.assertAlmostEqual(metrics['target_mean'],expected,places=5)

    def test_terminal_target_does_not_bootstrap(self):
        for double in (False,True):
            online=ConstantQ([1.,5.,2.]);target=ConstantQ([1000.,200.,0.])
            batch=(torch.zeros(1,209),torch.tensor([0]),torch.tensor([3.]),torch.zeros(1,209),torch.tensor([1.]))
            m=dqn_update(online,target,torch.optim.SGD(online.parameters(),lr=0),batch,.9,double)
            self.assertEqual(m['target_mean'],3.)

    def test_time_limit_bootstraps_but_resets_gae_recursion(self):
        advantage,returns=generalized_advantages(torch.tensor([1.,1.]),torch.tensor([2.,3.]),
            torch.tensor([5.,7.]),torch.tensor([0.,1.]),torch.tensor([1.,1.]),.9,.95)
        self.assertTrue(torch.allclose(advantage,torch.tensor([3.5,-2.])))
        self.assertTrue(torch.allclose(returns,torch.tensor([5.5,1.])))

    def test_gae_accumulates_within_episode(self):
        advantage,_=generalized_advantages(torch.tensor([1.,1.]),torch.tensor([2.,3.]),
            torch.tensor([3.,7.]),torch.tensor([0.,1.]),torch.tensor([0.,1.]),.9,.95)
        self.assertTrue(torch.allclose(advantage,torch.tensor([-.01,-2.]),atol=1e-6))

    def test_json_export_matches_torch_on_many_inputs(self):
        torch.manual_seed(42);network=QNetwork(209)
        inputs=np.random.default_rng(59).normal(size=(100,209)).astype(np.float32)
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'model.json';export_model(network,file,{})
            model=json.loads(file.read_text())
        x=inputs.astype(np.float64)
        for layer in model['layers']:
            x=x @ np.asarray(layer['weights']).T + np.asarray(layer['bias'])
            if layer['activation']=='relu':x=np.maximum(x,0)
        with torch.inference_mode():expected=network(torch.from_numpy(inputs)).numpy()
        self.assertLess(np.max(np.abs(expected-x)),1e-6)
        self.assertTrue(np.array_equal(expected.argmax(1),x.argmax(1)))

if __name__=='__main__':
    unittest.main()
