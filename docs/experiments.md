# Reproducible experiments

The default experiment fixes 32 neurons, horizon 256, three seeds
`20261112..20261114`, five uniform input-event probabilities `0, .01, .1, .5, 1`
and one burst pattern. Each runs with a final-only query and queries every eight
ticks plus the horizon. Nonzero currents are uniform integers `1..255`; initial
states are uniform integers `0..255`. These are synthetic workloads, not estimates
of activity in a brain or a realistic SNN.

For every configuration, both models must match **all** spikes, queries, and final
states before its timing is accepted. The JSON records exact parameters, fixture
and output SHA256 values, interpreter/system, and every raw timing sample. The
CSV is a scalar summary of the same run. A ratio `event_over_dense_time > 1`
means the event implementation was slower on that measured case.

Three repetitions are summarized by a median. The timer includes model input
validation, per-invocation jump-table construction, computation and output
construction. Fixture generation, JSON/hashing and explicit garbage collection
between repetitions are excluded equally. Model execution order alternates
across seeds. This is a small host-time experiment, not a statistically controlled
microbenchmark; interpreter and machine effects remain.

Do not expect bit-identical timing files. Exact numerical checksums should match
for unchanged code/parameters; wall times and full JSON hashes should vary.
The repository does not fit a switching threshold on this matrix or claim an
online selector. A source-controlled `results/demo.json` is an example local run,
not a promise that another machine will show the same crossover.

Useful next experiments: increase query frequency while holding events fixed;
replace random input with frozen adversarial patterns; separate table startup
from steady-state cost in a separately labeled measurement. Keep the complete
matrix and explain negative results instead of reporting only the fastest case.
