# DriftLatch identity and review gate

## Mechanism signature

A permissionless semantic drift latch for a mutable, bounded source window. The owner establishes a validator-fetched baseline. Any wallet can request a fresh check. Exact source receipts separate unchanged content, changes outside the watched window, unavailable sources, editorial edits, and material rule changes. Material drift latches the watch until the owner adopts a still-current checked receipt.

## Mechanism separation

| Earlier mechanism | Core operation | DriftLatch difference |
| --- | --- | --- |
| SourceSeal / CiteGuard | Decide whether evidence supports one claim | Repeatedly observe one mutable authority and classify change over time |
| MergeLedger / InvariantGate | Compare caller-submitted revisions | Fetch the current external source permissionlessly; callers cannot supply the candidate text |
| Threadmark | Grow an immutable claim-provenance graph | Maintain a replaceable baseline with a latched drift state and adoption guard |
| IntentLock | Detect semantically duplicate agent actions | Detect semantic change in externally published rules |

## Contract identity

- Metaphor: a tamper-evident tripwire, not a courtroom or scoring rubric.
- State rhythm: establish, observe, latch, adopt, archive.
- Consensus question: did the selected external text change the behavior named in the frozen materiality rule?
- Stored decision surface: one bounded verdict only. Source availability, full-file digest, and selected excerpt are strict-equality receipts.
- Authority: checks are permissionless; only the owner may replace the baseline or archive the watch.

## Pre-deployment readiness

| Requirement | Code path | Targeted test | Live proof | Status |
| --- | --- | --- | --- | --- |
| Exact hostname/path parsing and mutable source identity | `_source_url` | hostile host and commit-SHA rejection | Pending | UNVERIFIED |
| Independent source fetch and exact receipt | `_fetch_receipt`, `strict_eq` | changed validator snapshot rejection | Pending | UNVERIFIED |
| Semantic materiality consensus checks all state-driving output | `check_drift`, comparative principle | forged editorial result rejection | Pending | UNVERIFIED |
| Unavailable and outside-window changes are explicit | `check_drift` | 404 and appendix-only tests | Pending | UNVERIFIED |
| Adoption cannot use a stale or foreign check | `adopt_check` | owner, replay, and latest-check guards | Pending | UNVERIFIED |
| Terminal archive | `archive_watch` | unauthorized and post-archive rejection | Pending | UNVERIFIED |
