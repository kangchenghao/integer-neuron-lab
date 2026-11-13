"""Exact integer transition and a deliberately straightforward dense simulator.

Time zero contains the supplied initial state. At each positive integer tick,
each neuron leaks once, receives that tick's current, and may emit one spike.
There are no recurrent connections, bias, residual current, or learning rules.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Event:
    """An already aggregated current at a tick and a zero-based neuron ID.

    Simulators validate the time/ID against their run. Zero-current records
    are valid, though a producer may omit them.
    """

    time: int
    neuron: int
    current: int


@dataclass(frozen=True, slots=True)
class Spike:
    time: int
    neuron: int


@dataclass(frozen=True, slots=True)
class StateQuery:
    time: int
    states: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class SimulationResult:
    spikes: tuple[Spike, ...]
    queries: tuple[StateQuery, ...]
    final_states: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class StepResult:
    state: int
    spike: bool
    u: int


EventInput = Event | tuple[int, int, int]


def _integer(value: int, name: str) -> int:
    # bool is an int subclass, but accepting it obscures input mistakes.
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer")
    return value


def _u8(value: int, name: str) -> int:
    _integer(value, name)
    if not 0 <= value <= 255:
        raise ValueError(f"{name} must be in 0..255")
    return value


def one_step(state: int, current: int) -> StepResult:
    """Return the exact u8 transition, including the clamped potential u."""
    _u8(state, "state")
    _u8(current, "current")
    u = min((230 * state) // 256 + current, 255)
    spike = u >= 127
    return StepResult(0 if spike else u, spike, u)


def _prepare_inputs(
    initial_states: Iterable[int],
    horizon: int,
    events: Iterable[EventInput],
    query_times: Iterable[int],
) -> tuple[tuple[int, ...], tuple[Event, ...], tuple[int, ...]]:
    """Shared input parsing only; simulation arithmetic is not shared."""
    _integer(horizon, "horizon")
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    initial = tuple(initial_states)
    if not initial:
        raise ValueError("at least one initial state is required")
    for value in initial:
        _u8(value, "initial state")

    canonical: list[Event] = []
    previous = (0, -1)
    for record in events:
        if isinstance(record, Event):
            event = record
        else:
            if not isinstance(record, tuple) or len(record) != 3:
                raise TypeError("each event must be Event or a (time, neuron, current) tuple")
            event = Event(*record)
        _integer(event.time, "event time")
        _integer(event.neuron, "event neuron")
        _u8(event.current, "event current")
        if not 1 <= event.time <= horizon:
            raise ValueError("event time must be in 1..horizon")
        if not 0 <= event.neuron < len(initial):
            raise ValueError("event neuron is outside the initial-state array")
        key = (event.time, event.neuron)
        if key <= previous:
            raise ValueError("events must be unique and strictly ordered by (time, neuron)")
        previous = key
        canonical.append(event)

    queries = tuple(query_times)
    if not queries:
        raise ValueError("query_times must include the horizon")
    previous_query = 0
    for time in queries:
        _integer(time, "query time")
        if not previous_query < time <= horizon:
            raise ValueError("query times must be unique, strictly increasing, and in 1..horizon")
        previous_query = time
    if queries[-1] != horizon:
        raise ValueError("the last query time must equal the horizon")
    return initial, tuple(canonical), queries


def simulate_dense(
    initial_states: Iterable[int],
    horizon: int,
    events: Iterable[EventInput],
    query_times: Iterable[int],
) -> SimulationResult:
    """Visit every neuron at every tick using the canonical event input.

    No input expansion is supplied by the caller. Events at a tick are applied
    as part of that tick's one update, before any state query at that tick.
    """
    initial, records, times = _prepare_inputs(initial_states, horizon, events, query_times)
    states = list(initial)
    spikes: list[Spike] = []
    observations: list[StateQuery] = []
    cursor = query_cursor = 0
    for time in range(1, horizon + 1):
        for neuron in range(len(states)):
            current = 0
            if cursor < len(records):
                event = records[cursor]
                if (event.time, event.neuron) == (time, neuron):
                    current = event.current
                    cursor += 1
            # Inputs were validated once at the boundary. Repeating the public
            # one_step type/range checks on every dense tick would make an
            # implementation cost look like an event-algorithm advantage.
            potential = (230 * states[neuron]) // 256 + current
            if potential > 255:
                potential = 255
            if potential >= 127:
                states[neuron] = 0
                spikes.append(Spike(time, neuron))
            else:
                states[neuron] = potential
        if query_cursor < len(times) and times[query_cursor] == time:
            observations.append(StateQuery(time, tuple(states)))
            query_cursor += 1
    return SimulationResult(tuple(spikes), tuple(observations), tuple(states))
