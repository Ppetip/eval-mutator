# SPDX-License-Identifier: GPL-3.0-only
"""Plan JSON formatting probes and evaluate explicitly supplied output relations."""
import argparse
from collections import Counter
import hashlib
import json
from io_utils import canonical, load, shape, text


def plan(data):
    shape(data, {"tasks"})
    if not isinstance(data["tasks"], list) or len(data["tasks"]) > 100:
        raise ValueError("tasks must be an array of at most 100")
    seen = set()
    for task in data["tasks"]:
        shape(task, {"id", "input"}); text(task["id"])
        if task["id"] in seen or not isinstance(task["input"], dict):
            raise ValueError("duplicate id or task input is not an object")
        seen.add(task["id"])
    canonical(data)
    probes = []
    cases = []
    for task in data["tasks"]:
        original = canonical(task["input"])
        variant = json.dumps(dict(reversed(sorted(task["input"].items()))), indent=2, ensure_ascii=True, allow_nan=False)
        probes.append({"id": task["id"], "original_input": original, "variant_input": variant,
                       "input_sha256": hashlib.sha256(original.encode()).hexdigest()})
        cases.append({"id": task["id"], "relation": "equal", "before": None, "after": None, "observed": False})
    return {"mode": "offline-probe-plan", "probes": probes, "evaluation_template": {"cases": cases},
            "limitation": "Formatting and top-level key order change; JSON values do not. Confirm invariance fits your task, collect actual model outputs separately, and set observed true only after filling both outputs. No model calls are made."}


def evaluate(data):
    shape(data, {"cases"})
    cases = data["cases"]
    if not isinstance(cases, list) or len(cases) > 1000:
        raise ValueError("cases must be an array of at most 1000")
    seen = set()
    for case in cases:
        shape(case, {"id", "relation", "before", "after", "observed"}); text(case["id"])
        if case["id"] in seen:
            raise ValueError("duplicate case id")
        seen.add(case["id"])
        if case["observed"] is not True:
            raise ValueError("unobserved template: fill both outputs before evaluation")
        if not isinstance(case["relation"], str) or case["relation"] not in {"equal", "unordered", "nondecreasing"}:
            raise ValueError("unknown relation")
        for key in ("before", "after"):
            value = case[key]
            if case["relation"] == "unordered" and not isinstance(value, list):
                raise ValueError("unordered relation requires arrays")
            if case["relation"] == "nondecreasing" and type(value) not in (int, float):
                raise ValueError("nondecreasing requires finite numbers")
    canonical(data)
    results = []
    for case in cases:
        left, right = case["before"], case["after"]
        relation = case["relation"]
        passed = canonical(left) == canonical(right) if relation == "equal" else Counter(map(canonical, left)) == Counter(map(canonical, right)) if relation == "unordered" else right >= left
        results.append({"id": case["id"], "relation": relation, "passed": passed,
                        "before_sha256": hashlib.sha256(canonical(left).encode()).hexdigest(),
                        "after_sha256": hashlib.sha256(canonical(right).encode()).hexdigest()})
    passed = sum(r["passed"] for r in results)
    return {"mode": "offline-relation-evaluation", "evaluated": len(results), "passed": passed,
            "pass_rate": passed / len(results) if results else None, "cases": results,
            "limitation": "Consistency with a supplied relation is not answer correctness. Two wrong answers can agree. Observed is a caller declaration, not evidence provenance or independent review."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "evaluate"])
    parser.add_argument("--input", required=True)
    parser.add_argument("--check", action="store_true", help="For evaluate, exit 1 on a relation failure")
    args = parser.parse_args()
    if args.check and args.command != "evaluate":
        parser.error("--check requires evaluate")
    try:
        result = (plan if args.command == "plan" else evaluate)(load(args.input))
        print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, TypeError, OSError, RecursionError) as error:
        parser.error(str(error))
    if args.check and result["passed"] < result["evaluated"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
