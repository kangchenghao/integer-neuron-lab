# Recorded local validation

Validation date: 2026-11-12. Environment: CPython 3.13.6, Windows AMD64.

- 23 unittest methods passed: 19 numerical/input-contract checks and 4 offline CLI integration checks.
- The checks include all 65,536 one-step state/current pairs, plus all 65,536 pairs through both H=1 simulators. These are finite checks, not exhaustive event-sequence verification.
- `results/verification.json`: 40 seeded random problems; every spike, query state and final state agreed.
- `results/demo.json`: 36 configurations, 216 timed model invocations; all corresponding outputs agreed.
- Independent review found a `.csv` output collision in the CLI; it was fixed, with a sentinel-file non-overwrite regression test.
- A wheel was built successfully in an isolated build environment. The source launcher requires no package installation.
- The workflow targets Python 3.10/3.13 on Windows/Ubuntu, but hosted CI has not yet run. Python 3.10 syntax parsing is not a substitute for running on that interpreter.

## Example host-time snapshot

The entries below are medians across the three per-seed ratios. They describe only the checked-in local run; see all raw samples in JSON. A value greater than one means event processing was slower.

|Synthetic event probability/pattern|Final-only query: event/dense|Every-8 query: event/dense|
|---|---:|---:|
|0|0.114|0.668|
|0.01|0.133|0.458|
|0.1|0.426|0.592|
|0.5|1.031|0.947|
|1|1.148|1.176|
|burst|0.356|0.773|

These ratios are not a fitted policy, universal crossover, speedup guarantee, or hardware measurement. Source hashes bind the run to its implementation.
