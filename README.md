# Eval Mutator

**Find inconsistent model behavior when you cannot label every answer.**

A dependency-free planner and scorer for controlled input variations. Generate JSON formatting probes, collect model outputs separately, then test explicit relations between those outputs. It never calls a model or fills in answers for you.

## Try it

Python 3.11+; no installation or API key required.

```sh
python app.py plan --input examples/tasks.json
python app.py evaluate --input examples/demo.json
python app.py evaluate --input examples/demo.json --check
python -m unittest discover -s tests -v
python verify_demos.py
```

The authored synthetic output fixture passes two of three relations. One deliberately loses a repeated item and fails. `--check` therefore exits 1. This is a scorer demonstration, not measured LLM performance.

## Plan probes

Supply `tasks`, an array of at most 100 objects with unique nonempty `id` and an `input` JSON object. `plan` emits compact JSON and a variant with whitespace and top-level key order changed. Parsed JSON values stay equal. Confirm that this invariance is appropriate for your task: formatting itself may matter in some workflows.

The result also contains `evaluation_template`. Copy that object into a separate local file, run your chosen model or system independently, fill `before` and `after`, and set `observed` to true. Unfilled templates use `observed: false` and are rejected by the evaluator, preventing two placeholder nulls from being counted as a pass. No automatic provider integration is enabled.

## Evaluate outputs

Supply `cases`, an array of at most 1,000 objects, each with unique nonempty `id`, `relation`, `before`, `after` and `observed: true`.

| Relation | Meaning |
|---|---|
| `equal` | Canonical JSON equality; object key order ignored, array order retained, booleans and numbers distinct |
| `unordered` | Arrays contain the same JSON values with the same multiplicities; order ignored |
| `nondecreasing` | Finite numeric `after` is at least `before`; booleans rejected |

Reports give case outcomes, hashes of supplied outputs and a pass rate. Empty batches return null for rate. Raw model outputs are omitted from evaluation reports; case IDs and hashes still require appropriate handling. Probe plans contain input text and must stay private for authorized private inputs.

The CLI caps UTF-8 input at 1 MiB and rejects duplicate keys, nonfinite values, duplicate IDs, unsupported fields, wrong types and unobserved cases. Invalid batches exit 2 with no result. Evaluation normally exits 0; `--check` exits 1 for failed relations and is valid only with `evaluate`. No file writes or model/tool execution occur.

## Evidence and limits

11 local tests and 6 CLI contracts pass: order changes, duplicate-item loss, boolean/number distinctions, monotonic direction, empty batches, malformed late cases and rejecting unfinished templates. All four Windows/Linux Python 3.11/3.13 jobs passed on GitHub Actions. [Hosted verification](https://github.com/Ppetip/eval-mutator/actions/runs/36965546938).

Two wrong answers can agree. A passed relation is not answer correctness, independent ground truth or proof the model is robust. `observed` is the caller's declaration, not verified provenance. Tests use only synthetic authored outputs.

Next: independently reviewed task-specific relations, recorded output provenance and additional transformations whose assumptions can be checked. No LLM training or paid inference is part of this version.

Original code: GPL-3.0-only. See [LICENSE](LICENSE).
