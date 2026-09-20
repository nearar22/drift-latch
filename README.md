# DriftLatch

## The tripwire

A mutable policy can change without changing its URL. Systems that trust that URL usually notice too late. DriftLatch stores a validator-fetched baseline for a bounded source window, lets anyone request a fresh observation, and latches when the meaning named by the owner has changed.

The contract is deliberately narrower than a general claim verifier. It does not decide whether a policy is good or authoritative. It answers one reusable question: has this exact published source changed in a way that alters the behavior covered by the frozen materiality rule?

## Five possible readings

- `IDENTICAL`: the full source digest still matches the baseline.
- `OUTSIDE_WINDOW`: the file changed, but the watched lines did not.
- `EDITORIAL`: the watched wording changed without changing governed behavior.
- `MATERIAL`: an obligation, permission, prohibition, threshold, deadline, interface, or other rule named by the watch changed.
- `UNAVAILABLE`: the source could not produce a usable receipt. Unavailability never becomes evidence of stability.

A material verdict changes the watch from `MONITORED` to `DRIFTED`. The owner may adopt only the latest eligible check, and adoption refetches the source through strict equality before replacing the baseline. A stale observation cannot be installed after the page changes again. Archival is terminal.

## Why consensus matters

The source receipt and the semantic decision have different consensus boundaries. `strict_eq` makes validators independently retrieve the exact HTTP status, whole-file SHA-256, and selected excerpt. Only after that receipt is stable does comparative consensus classify a changed excerpt. The only model-generated value stored is the bounded `EDITORIAL` or `MATERIAL` verdict. No unchecked explanation, score, or narrative can influence state.

The URL parser accepts only HTTPS file endpoints on the exact GitHub Contents API host and path shape. It rejects credentials, ports, caller-controlled queries, fragments, traversal, and encoded path tricks. Each operation adds its own bounded cache key, then validators decode the API's base64 file content before hashing and comparing it.

## Lifecycle

```text
create_watch -> MONITORED
                   |
          permissionless check_drift
                   |
        +----------+-----------+
        |                      |
  IDENTICAL / EDITORIAL     MATERIAL
        |                      |
    MONITORED               DRIFTED
                               |
                    owner adopts latest receipt
                               |
                           MONITORED

owner archive_watch -> ARCHIVED
```

## Reproduce the review

Install the pinned Python packages from `requirements.txt`, then run:

```bash
python -m pytest tests -q
genvm-lint lint contracts/drift_latch.py --json
```

The suite exercises the complete baseline, material drift, and adoption path plus source failure, changes outside the selected window, hostile URL parsing, duplicate IDs, stale adoption, unauthorized owner actions, strict receipt disagreement, forged semantic classification, and terminal archive behavior.

Node scripts use `genlayer-js@2.0.0-rc.1` against Studio Next. Keep `GENLAYER_PRIVATE_KEY` in the process environment, never in this repository.

```bash
npm ci
npm run deploy
```

The finalized deployment and live mutation record will be added to `deployment.json` after the exact reviewed source is exercised on Studio Next.

## Trust boundary

The watch owner chooses the source and materiality rule. DriftLatch proves what validators fetched and how the selected text changed relative to that rule. It does not prove that the GitHub owner is independent, that the publisher has legal authority, or that an off-chain system obeyed the policy. The included refund file is an operator-controlled demo fixture, labeled as such.
