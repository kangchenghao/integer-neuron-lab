"""Exact zero-input composition and event-driven integer-neuron simulation."""
from __future__ import annotations

from collections.abc import Iterable

from .model import (
    EventInput,
    SimulationResult,
    Spike,
    StateQuery,
    _integer,
    _prepare_inputs,
)

JumpTable = tuple[tuple[int, ...], ...]


def build_jump_table(max_gap: int) -> JumpTable:
    """Build powers of the exact integer transition for one run.

    Row k applies 2**k successive floor operations on states 0..126. Rows
    stop early if a power maps every state to zero. This function has no
    module-level cache: event simulation includes its table construction.
    """
    _integer(max_gap, "max_gap")
    if max_gap < 0:
        raise ValueError("max_gap must be nonnegative")
    if max_gap == 0:
        return ()
    rows = [tuple((230 * state) // 256 for state in range(127))]
    while (1 << len(rows)) <= max_gap and any(rows[-1]):
        previous = rows[-1]
        rows.append(tuple(previous[previous[state]] for state in range(127)))
    return tuple(rows)


def _advance(state: int, gap: int, table: JumpTable) -> int:
    # Internal callers provide a normalized state and a table for the run's H.
    for row in table:
        if gap & 1:
            state = row[state]
        gap >>= 1
        if not gap or state == 0:
            return state
    if gap:
        # An early table stop is valid only after an all-zero power.
        if table and not any(table[-1]):
            return 0
        raise ValueError("jump table does not cover this gap")
    return state


def jump_decay(state: int, gap: int) -> int:
    """Apply exactly gap zero-input leaks to a normalized state 0..126.

    This composes repeated integer floors. It does not calculate a floating
    exponential or take just one floor after raising 230/256 to a power.
    A fresh table is built per public call; simulate_event builds once/run.
    """
    _integer(state, "state")
    _integer(gap, "gap")
    if not 0 <= state <= 126:
        raise ValueError("jump decay requires a normalized state in 0..126")
    if gap < 0:
        raise ValueError("gap must be nonnegative")
    return _advance(state, gap, build_jump_table(gap))


def simulate_event(
    initial_states: Iterable[int],
    horizon: int,
    events: Iterable[EventInput],
    query_times: Iterable[int],
) -> SimulationResult:
    """Process tick 1, then only event/query timestamps.

    Intermediate observations project state without moving its event anchor.
    The final observation at H materializes every retained state. Only input
    validation/result types are shared with the dense implementation.
    """
    initial, records, times = _prepare_inputs(initial_states, horizon, events, query_times)
    table = build_jump_table(horizon)
    states = list(initial)
    last_time = [1] * len(states)
    spikes: list[Spike] = []
    observations: list[StateQuery] = []
    cursor = 0

    # Arbitrary u8 initial values cannot be sent through the 0..126 table:
    # values >=142 can emit a spike even with no input at the first tick.
    currents = [0] * len(states)
    while cursor < len(records) and records[cursor].time == 1:
        event = records[cursor]
        currents[event.neuron] = event.current
        cursor += 1
    for neuron, value in enumerate(states):
        potential = (value * 230) // 256 + currents[neuron]
        if potential > 255:
            potential = 255
        if potential >= 127:
            states[neuron] = 0
            spikes.append(Spike(1, neuron))
        else:
            states[neuron] = potential

    query_cursor = 0
    if times[0] == 1:
        observations.append(StateQuery(1, tuple(states)))
        query_cursor = 1

    while query_cursor < len(times):
        query_time = times[query_cursor]
        time = min(records[cursor].time, query_time) if cursor < len(records) else query_time
        # All events at the timestamp precede the observation. Canonical ID
        # order also makes emitted spikes strictly ordered by (time, neuron).
        while cursor < len(records) and records[cursor].time == time:
            event = records[cursor]
            neuron = event.neuron
            leaked = _advance(states[neuron], time - last_time[neuron], table)
            potential = leaked + event.current
            if potential > 255:
                potential = 255
            if potential >= 127:
                states[neuron] = 0
                spikes.append(Spike(time, neuron))
            else:
                states[neuron] = potential
            last_time[neuron] = time
            cursor += 1
        if query_time == time:
            projected = tuple(
                _advance(value, time - last_time[neuron], table)
                for neuron, value in enumerate(states)
            )
            observations.append(StateQuery(time, projected))
            if time == horizon:
                states[:] = projected
                last_time[:] = [time] * len(states)
            query_cursor += 1

    return SimulationResult(tuple(spikes), tuple(observations), tuple(states))
