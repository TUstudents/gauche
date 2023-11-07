"""
Unit tests for the Weisfeiler Lehman graph kernel.
"""

import pytest
import torch
import gpytorch
from gauche import SIGP, NonTensorialInputs
from gauche.kernels.graph_kernels import WeisfeilerLehmanKernel
from gauche.dataloader import MolPropLoader
import graphein.molecule as gm

graphein_config = gm.MoleculeGraphConfig(
    node_metadata_functions=[gm.total_degree],
    edge_metadata_functions=[gm.add_bond_type],
)


@pytest.mark.parametrize(
    "node_label",
    ["element", "total_degree", "XYZ", None, 1],
)
def test_weisfeiler_lehman_kernel_node_label(node_label):
    """
    Test if Weisfeiler Lehman kernel works as intended
    when using node labels.
    """

    class GraphGP(SIGP):
        def __init__(self, train_x, train_y, likelihood):
            super().__init__(train_x, train_y, likelihood)
            self.mean = gpytorch.means.ConstantMean()
            self.covariance = WeisfeilerLehmanKernel(node_label=node_label)

        def forward(self, x):
            mean = self.mean(torch.zeros(len(x), 1)).float()
            covariance = self.covariance(x)

            # for numerical stability
            jitter = max(covariance.diag().mean().detach().item() * 1e-4, 1e-4)
            covariance += torch.eye(len(x)) * jitter
            return gpytorch.distributions.MultivariateNormal(mean, covariance)

    loader = MolPropLoader()
    loader.load_benchmark("Photoswitch")
    loader.featurize("molecular_graphs", graphein_config=graphein_config)

    X = NonTensorialInputs(loader.features)
    likelihood = gpytorch.likelihoods.GaussianLikelihood()
    model = GraphGP(X, loader.labels, likelihood)

    model.train()
    likelihood.train()

    if node_label in ["element", "total_degree"]:
        output = model(X)
    else:
        with pytest.raises(Exception):
            output = model(X)


@pytest.mark.parametrize(
    "edge_label",
    ["bond_type", "bond_type_and_total_degree", None, 1],
)
def test_weisfeiler_lehman_kernel_edge_label(edge_label):
    """
    Test if Weisfeiler Lehman kernel also works when
    using edge labels.
    """

    class GraphGP(SIGP):
        def __init__(self, train_x, train_y, likelihood):
            super().__init__(train_x, train_y, likelihood)
            self.mean = gpytorch.means.ConstantMean()
            self.covariance = WeisfeilerLehmanKernel(
                node_label="element", edge_label=edge_label
            )

        def forward(self, x):
            mean = self.mean(torch.zeros(len(x), 1)).float()
            covariance = self.covariance(x)

            # for numerical stability
            jitter = max(covariance.diag().mean().detach().item() * 1e-4, 1e-4)
            covariance += torch.eye(len(x)) * jitter
            return gpytorch.distributions.MultivariateNormal(mean, covariance)

    loader = MolPropLoader()
    loader.load_benchmark("Photoswitch")
    loader.featurize("molecular_graphs", graphein_config=graphein_config)

    X = NonTensorialInputs(loader.features)
    likelihood = gpytorch.likelihoods.GaussianLikelihood()
    model = GraphGP(X, loader.labels, likelihood)

    model.train()
    likelihood.train()

    if edge_label == "bond_type" or edge_label == None:
        output = model(X)
    else:
        with pytest.raises(Exception):
            output = model(X)
