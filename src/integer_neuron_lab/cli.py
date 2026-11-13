"""A small reproducibility entry point, separate from the mathematical models."""
import argparse
import csv
from dataclasses import asdict
import gc
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import time

from . import Event, simulate_dense, simulate_event


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def checksum(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def make_case(n, horizon, activity, query_mode, seed):
    """Synthesize inputs; density is a workload parameter, not brain evidence."""
    rng = random.Random(seed)
    initial = tuple(rng.randrange(256) for _ in range(n))
    currents = []
    for tick in range(1, horizon + 1):
        probability = (0.75 if tick <= max(1, horizon // 8) else 0.0) if activity == "burst" else float(activity)
        for neuron in range(n):
            if rng.random() < probability:
                currents.append(Event(tick, neuron, rng.randrange(1, 256)))
    queries = [horizon] if query_mode == "final" else sorted(set(range(8, horizon + 1, 8)) | {horizon})
    return initial, tuple(currents), tuple(queries)


def environment():
    # Record platform information without personal identifiers.
    return {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "system": platform.system(), "machine": platform.machine()}


def source_fingerprints():
    package = Path(__file__).resolve().parent
    root = package.parent.parent
    files = sorted(package.glob("*.py"))
    if (root / "run.py").is_file():
        files.append(root / "run.py")
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def result_payload(result):
    return asdict(result)


def measure(fn, args, repeats):
    elapsed = []
    reference = None
    for _ in range(repeats):
        gc.collect()
        start = time.perf_counter_ns()
        result = fn(*args)
        elapsed.append(time.perf_counter_ns() - start)
        payload = result_payload(result)
        if reference is None:
            reference = payload
        elif payload != reference:
            raise AssertionError("Repeated deterministic run changed output")
    return reference, elapsed


def verify(seed, cases):
    rng = random.Random(seed)
    records = []
    for index in range(cases):
        n, horizon = rng.randrange(1, 17), rng.randrange(1, 129)
        activity = rng.choice(["0", "0.01", "0.1", "0.5", "1", "burst"])
        mode = rng.choice(["final", "every8"])
        initial, events, queries = make_case(n, horizon, activity, mode, rng.randrange(1 << 32))
        args = (initial, horizon, events, queries)
        dense = result_payload(simulate_dense(*args))
        event = result_payload(simulate_event(*args))
        if dense != event:
            raise AssertionError(f"Dense/event mismatch in case {index}")
        records.append({"n": n, "horizon": horizon, "events": len(events), "output_sha256": checksum(dense)})
    return {"passed": True, "seed": seed, "cases": cases, "environment": environment(),
            "source_sha256": source_fingerprints(), "records": records}


def experiment(destination, n, horizon, repeats):
    if destination.suffix.lower() != ".json":
        raise ValueError("experiment output must end in .json; CSV is a separate sibling file")
    rows = []
    for seed in (20261112, 20261113, 20261114):
        for activity in ("0", "0.01", "0.1", "0.5", "1", "burst"):
            for query_mode in ("final", "every8"):
                initial, events, queries = make_case(n, horizon, activity, query_mode, seed)
                args = (initial, horizon, events, queries)
                # Alternate order across seeds to expose some order sensitivity;
                # this is a small host-time experiment, not a controlled CPU study.
                functions = [("dense", simulate_dense), ("event", simulate_event)]
                if seed % 2:
                    functions.reverse()
                measured = {name: measure(fn, args, repeats) for name, fn in functions}
                dense, dense_ns = measured["dense"]
                event, event_ns = measured["event"]
                if dense != event:
                    raise AssertionError("Benchmark outputs differ; timing result rejected")
                fixture = {"initial": initial, "horizon": horizon, "events": [asdict(e) for e in events], "queries": queries}
                rows.append({"seed": seed, "activity": activity, "query_mode": query_mode,
                    "neurons": n, "horizon": horizon, "input_events": len(events),
                    "actual_input_density": len(events) / (n * horizon), "query_count": len(queries),
                    "spike_count": len(dense["spikes"]), "all_outputs_exact": True,
                    "fixture_sha256": checksum(fixture), "output_sha256": checksum(dense),
                    "dense_ns": dense_ns, "event_ns": event_ns,
                    "dense_median_ns": statistics.median(dense_ns), "event_median_ns": statistics.median(event_ns),
                    "event_over_dense_time": statistics.median(event_ns) / statistics.median(dense_ns)})
    report = {"schema": "integer-neuron-experiment-v1", "all_outputs_exact": True, "environment": environment(),
        "source_sha256": source_fingerprints(),
        "parameters": {"neurons": n, "horizon": horizon, "repeats": repeats},
        "measurement": {"included": ["model input validation", "event model jump-table construction per invocation", "state updates", "spike/query output construction", "final materialization"],
            "excluded": ["fixture generation", "JSON hashing/serialization", "explicit garbage collection between repeats"],
            "timer": "perf_counter_ns; median with all raw samples retained", "unit": "host Python nanoseconds, not hardware cycles or energy"},
        "limitations": ["Synthetic inputs only; no clinical, network or biophysical validation.",
            "Three fixed seeds and small workloads are an exploratory matrix, not statistical generalization.",
            "Both algorithms implement the same documented toy integer dynamics; neither is claimed novel.",
            "Frequent queries and dense events can erase the event method's advantage.",
            "Host timings vary by interpreter, machine, ordering, load and run."], "rows": rows}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    csv_file = destination.with_suffix(".csv")
    scalar = [{k: v for k, v in r.items() if not isinstance(v, list)} for r in rows]
    with csv_file.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(scalar[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(scalar)
    return {"passed": True, "configurations": len(rows), "model_invocations": len(rows) * 2 * repeats,
            "result": destination.name, "csv": csv_file.name}


def positive(text):
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("verify", help="compare independent dense/event implementations on generated inputs")
    check.add_argument("--seed", type=int, default=20261112)
    check.add_argument("--cases", type=positive, default=40)
    check.add_argument("--output", type=Path, help="optionally save the verification record")
    bench = commands.add_parser("experiment", help="write a seeded numerical-equivalence and host-time matrix")
    bench.add_argument("--output", type=Path, default=Path("results/demo.json"))
    bench.add_argument("--neurons", type=positive, default=32)
    bench.add_argument("--horizon", type=positive, default=256)
    bench.add_argument("--repeats", type=positive, default=3)
    args = parser.parse_args(argv)
    if args.output is not None and args.output.suffix.lower() != ".json":
        parser.error("--output must end in .json; CSV is written to a separate sibling file")
    if args.command == "verify":
        report = verify(args.seed, args.cases)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2))
    else:
        if args.neurons * args.horizon > 1_048_576:
            parser.error("neurons*horizon exceeds the small-experiment limit of 1,048,576")
        print(json.dumps(experiment(args.output, args.neurons, args.horizon, args.repeats), indent=2))
    return 0
