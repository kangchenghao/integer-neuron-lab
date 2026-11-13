"""Independent numerical golden checks and dense/event contract regressions."""
import random
import unittest
from unittest import mock

from integer_neuron_lab import (
    Event, Spike, StateQuery, build_jump_table, jump_decay, one_step,
    simulate_dense, simulate_event,
)
import integer_neuron_lab.events as event_module


class TransitionTests(unittest.TestCase):
    def test_all_65536_state_current_pairs(self):
        for state in range(256):
            # Independent integer identity: floor(230*v/256) equals
            # v-ceil(26*v/256), rather than sharing model.one_step arithmetic.
            expected_leak = state - (26 * state + 255) // 256
            for current in range(256):
                potential = min(expected_leak + current, 255)
                fired = potential >= 127
                actual = one_step(state, current)
                self.assertEqual((actual.state, actual.spike, actual.u),
                                 (0 if fired else potential, fired, potential), (state, current))

    def test_threshold_saturation_and_first_tick(self):
        self.assertEqual((one_step(0, 126).state, one_step(0, 126).spike), (126, False))
        self.assertEqual((one_step(0, 127).state, one_step(0, 127).spike), (0, True))
        self.assertEqual(one_step(255, 255).u, 255)
        self.assertFalse(one_step(141, 0).spike)
        self.assertTrue(one_step(142, 0).spike)

    def test_invalid_transition_arguments(self):
        for invalid in (-1, 256):
            with self.assertRaises(ValueError): one_step(invalid, 0)
            with self.assertRaises(ValueError): one_step(0, invalid)
        for invalid in (True, 1.5, "1", None):
            with self.assertRaises(TypeError): one_step(invalid, 0)
            with self.assertRaises(TypeError): one_step(0, invalid)


class JumpTests(unittest.TestCase):
    def test_entire_normalized_domain_against_repeated_leak(self):
        for initial in range(127):
            expected = initial
            for gap in range(65):
                self.assertEqual(jump_decay(initial, gap), expected, (initial, gap))
                expected -= (26 * expected + 255) // 256

    def test_random_gaps_and_composition(self):
        rng = random.Random(20261112)
        for _ in range(300):
            value = rng.randrange(127)
            gap = rng.randrange(2049)
            expected = value
            for _ in range(gap): expected = (expected * 230) // 256
            self.assertEqual(jump_decay(value, gap), expected)
            a, b = rng.randrange(80), rng.randrange(80)
            self.assertEqual(jump_decay(jump_decay(value, a), b), jump_decay(value, a + b))

    def test_boundary_gaps_and_large_exact_integer_time(self):
        self.assertEqual(jump_decay(126, 0), 126)
        self.assertEqual(jump_decay(126, 28), 1)
        self.assertEqual(jump_decay(126, 29), 0)
        self.assertEqual(jump_decay(126, 30), 0)
        self.assertEqual(jump_decay(126, 10**100), 0)
        self.assertEqual(build_jump_table(0), ())
        table = build_jump_table(128)
        self.assertTrue(all(len(row) == 127 for row in table))
        self.assertTrue(all(value == 0 for value in table[-1]))

    def test_single_final_floor_is_not_exact_composition(self):
        self.assertEqual((2 * 230**2) // 256**2, 1)
        self.assertEqual(jump_decay(2, 2), 0)
        result = simulate_event([2], 2, [Event(2, 0, 126)], [2])
        self.assertEqual(result.spikes, ())
        self.assertEqual(result.final_states, (126,))
        self.assertEqual(result, simulate_dense([2], 2, [Event(2, 0, 126)], [2]))

    def test_invalid_jump_arguments(self):
        for value in (-1, 127, 255):
            with self.assertRaises(ValueError): jump_decay(value, 1)
        with self.assertRaises(ValueError): jump_decay(1, -1)
        with self.assertRaises(ValueError): build_jump_table(-1)
        with self.assertRaises(TypeError): jump_decay(True, 1)
        with self.assertRaises(TypeError): jump_decay(1, 1.5)


class SimulationTests(unittest.TestCase):
    def test_h1_simulators_cover_every_state_current_pair(self):
        initial = list(range(256))
        for current in range(256):
            records = [Event(1, neuron, current) for neuron in range(256)]
            expected_states = tuple(one_step(value, current).state for value in initial)
            expected_spikes = tuple(Spike(1, neuron) for neuron, value in enumerate(initial) if one_step(value, current).spike)
            for simulate in (simulate_dense, simulate_event):
                result = simulate(initial, 1, records, [1])
                self.assertEqual(result.final_states, expected_states)
                self.assertEqual(result.spikes, expected_spikes)
                self.assertEqual(result.queries, (StateQuery(1, expected_states),))

    def test_no_input_initial_spikes_at_true_timestamp(self):
        initial = [0, 126, 127, 128, 141, 142, 200, 255]
        for simulate in (simulate_dense, simulate_event):
            result = simulate(initial, 1, [], [1])
            self.assertEqual(result.spikes, (Spike(1, 5), Spike(1, 6), Spike(1, 7)))
            self.assertEqual(result.final_states, (0, 113, 114, 115, 126, 0, 0, 0))
            self.assertEqual(result.queries, (StateQuery(1, result.final_states),))
            long_result = simulate(initial, 64, [], [1, 2, 8, 64])
            self.assertEqual(long_result.spikes, result.spikes)
            self.assertEqual(long_result.final_states, (0,) * len(initial))

    def test_events_precede_queries_and_spikes_are_ordered(self):
        events = [(1, 0, 127), (1, 2, 126), (2, 0, 126), (2, 1, 127), (3, 0, 14), (3, 2, 0)]
        for simulate in (simulate_dense, simulate_event):
            result = simulate([0, 0, 0], 3, events, [1, 2, 3])
            self.assertEqual(result.spikes, (Spike(1, 0), Spike(2, 1), Spike(3, 0)))
            self.assertEqual(result.queries, (
                StateQuery(1, (0, 0, 126)), StateQuery(2, (126, 0, 113)), StateQuery(3, (0, 0, 101))))
            self.assertEqual(result.final_states, (0, 0, 101))

    def test_queries_project_without_changing_anchor_and_final_materializes(self):
        original = event_module._advance
        calls = []
        def observe(value, gap, table):
            calls.append((value, gap))
            return original(value, gap, table)
        with mock.patch.object(event_module, "_advance", side_effect=observe):
            result = simulate_event([100], 4, [], [2, 3, 4])
        self.assertEqual(calls, [(89, 1), (89, 2), (89, 3)])
        self.assertEqual(result.queries, (StateQuery(2, (79,)), StateQuery(3, (70,)), StateQuery(4, (62,))))
        self.assertEqual(result.final_states, (62,))

    def test_gap_zero_at_event_query_and_h1(self):
        records = [Event(1, 0, 127), Event(2, 0, 10)]
        self.assertEqual(simulate_event([255], 2, records, [1, 2]), simulate_dense([255], 2, records, [1, 2]))
        for initial in range(256):
            for current in (0, 1, 126, 127, 255):
                events = [Event(1, 0, current)]
                self.assertEqual(simulate_event([initial], 1, events, [1]), simulate_dense([initial], 1, events, [1]))

    def test_table_is_built_once_per_simulation_not_globally_cached(self):
        with mock.patch.object(event_module, "build_jump_table", wraps=build_jump_table) as build:
            for _ in range(2): simulate_event([100, 0], 64, [Event(32, 0, 20)], [1, 8, 32, 64])
        self.assertEqual(build.call_count, 2)
        self.assertEqual(build.call_args_list, [mock.call(64), mock.call(64)])

    def test_zero_current_events_are_equivalent_to_omission(self):
        for simulate in (simulate_dense, simulate_event):
            plain = simulate([200, 126], 64, [(8, 1, 30)], [1, 8, 16, 64])
            explicit = simulate([200, 126], 64, [(1, 0, 0), (8, 1, 30), (16, 0, 0), (64, 1, 0)], [1, 8, 16, 64])
            self.assertEqual(explicit, plain)

    def test_fixed_seed_randomized_dense_event_equivalence(self):
        for seed in range(100):
            rng = random.Random(20261112 + seed)
            n, horizon = rng.randrange(1, 13), rng.randrange(1, 81)
            initial = [rng.randrange(256) for _ in range(n)]
            density = (0, .01, .1, .5, 1)[seed % 5]
            events = [Event(t, i, rng.randrange(256)) for t in range(1, horizon + 1) for i in range(n) if rng.random() < density]
            queries = sorted({horizon, *rng.sample(range(1, horizon + 1), rng.randrange(min(12, horizon) + 1))})
            self.assertEqual(simulate_event(initial, horizon, events, queries), simulate_dense(initial, horizon, events, queries), seed)

    def test_inputs_are_not_mutated_and_results_are_immutable_snapshots(self):
        initial, events, queries = [100, 0], [Event(2, 0, 20)], [1, 2, 4]
        before = (initial.copy(), events.copy(), queries.copy())
        result = simulate_event(initial, 4, events, queries)
        self.assertEqual((initial, events, queries), before)
        initial[0] = 0
        self.assertEqual(result.queries[0].states, (89, 0))
        with self.assertRaises((AttributeError, TypeError)):
            result.final_states = (0, 0)

    def test_iterable_inputs(self):
        result = simulate_event(iter([10, 20]), 2, iter([(2, 1, 7)]), iter([2]))
        self.assertEqual(result, simulate_dense([10, 20], 2, [Event(2, 1, 7)], [2]))


class InputValidationTests(unittest.TestCase):
    def test_invalid_initial_horizon_events_and_queries(self):
        bad = [
            ([], 2, [], [2]), ([256], 2, [], [2]), ([-1], 2, [], [2]), ([True], 2, [], [2]),
            ([0], 0, [], [1]), ([0], True, [], [1]), ([0], 1.5, [], [1]),
            ([0], 2, [(0, 0, 1)], [2]), ([0], 2, [(3, 0, 1)], [2]),
            ([0], 2, [(1, -1, 1)], [2]), ([0], 2, [(1, 1, 1)], [2]),
            ([0], 2, [(1, 0, -1)], [2]), ([0], 2, [(1, 0, 256)], [2]),
            ([0], 2, [(1, 0, True)], [2]), ([0], 2, [(True, 0, 1)], [2]),
            ([0], 2, [(1, False, 1)], [2]), ([0], 2, [(1, 0)], [2]),
            ([0], 2, [(1, 0, 2), (1, 0, 3)], [2]),
            ([0], 2, [(2, 0, 1), (1, 0, 1)], [2]),
            ([0, 0], 2, [(1, 1, 1), (1, 0, 1)], [2]),
            ([0], 2, [], []), ([0], 2, [], [1]), ([0], 2, [], [0, 2]),
            ([0], 2, [], [2, 1]), ([0], 2, [], [1, 1, 2]), ([0], 2, [], [3]),
            ([0], 2, [], [True, 2]), ([0], 2, [], [1.0, 2]),
        ]
        for simulate in (simulate_dense, simulate_event):
            for arguments in bad:
                with self.subTest(simulator=simulate.__name__, arguments=arguments):
                    with self.assertRaises((ValueError, TypeError)):
                        simulate(*arguments)


if __name__ == "__main__":
    unittest.main()
