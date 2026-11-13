# Numerical contract and exact skipping

The model is a finite-integer experiment, not a discretization claimed to
preserve a continuous biological model.

## Inputs and observations

- A nonempty sequence of initial states in `0..255` and a positive integer horizon `H`.
- Events `(time, neuron, current)` strictly sorted by `(time, neuron)`, with
  times `1..H`, valid neuron indices, and current `0..255`. Duplicate keys are
  rejected: callers must aggregate simultaneous inputs explicitly. Zero events
  are allowed and need not be stored by generators.
- Query times are strictly increasing in `1..H`, with the last query exactly `H`.
- Each tick applies the input and neuron update before queries at that tick.
  Spikes are ordered by `(time, neuron)`. Queries contain every neuron's state.
- Invalid inputs raise an error instead of being silently sorted, clipped, or
  interpreted differently by the two algorithms.

Every tick computes the equation in the README, using exact nonnegative integer
division. There is no wraparound; the intermediate sum saturates at 255 before
thresholding. Any nonspiking post-update state is at most 126, and a spike resets
it to zero.

## Why exact skipping is valid

After the first complete tick, all states lie in `0..126`. During a silent tick,
`g(v) = floor(230*v/256)` is nonincreasing, so no silent step can cross threshold
127. Silent intervals can therefore contain neither an unrecorded spike nor an
increase caused by an omitted input.

Build `J[0][v] = g(v)` and `J[k+1][v] = J[k][J[k][v]]`.
Induction gives `J[k][v] = g` composed `2**k` times. Decomposing the gap into
binary powers applies exactly the same state function as repeated tick updates;
it does not multiply a decay coefficient and round only once.

The first tick must be evaluated for every neuron because the initial state can
exceed 126. After normalization, each event advances from the last committed
anchor through a gap that includes the event tick's decay, then adds its input
and applies saturation/threshold/reset.

Intermediate queries evaluate `g**gap(anchor)` without committing a new anchor.
Function composition ensures future events and queries see the same state as
the dense reference. At the final query `H`, all states are materialized. This
argument depends on the exact stated dynamics; adding bias, signed input,
adaptation, or synaptic state requires a new argument.

## What checks can establish

Exhausting 65,536 one-step state/current pairs checks that finite function against
a separate arithmetic expression. It does not exhaust all event sequences.
Dense/event sequence checks provide additional implementation evidence under
specified seeds and boundaries. The composition argument explains exact jumping;
neither testing nor that argument validates biological behavior, neural-network
accuracy, or a hardware implementation.
