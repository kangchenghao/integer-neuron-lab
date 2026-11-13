"""A standard-library laboratory for exact finite-state neuron simulation."""

from .model import Event, SimulationResult, Spike, StateQuery, StepResult, one_step, simulate_dense
from .events import JumpTable, build_jump_table, jump_decay, simulate_event

__all__ = [
    "Event", "SimulationResult", "Spike", "StateQuery", "StepResult", "one_step",
    "simulate_dense", "JumpTable", "build_jump_table", "jump_decay", "simulate_event",
]
