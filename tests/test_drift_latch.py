import importlib
import base64
import json

CONTRACT = "contracts/drift_latch.py"
URL = "https://api.github.com/repos/acme/policy/contents/rules.txt"
BASE = "Refunds are available within 30 days.\nSupport is available by email."
CHANGED = "Refunds are available within 7 days.\nSupport is available by email."
RULE = "Treat changes to refund deadlines, eligibility, exclusions, or required steps as material."


def web(vm, body=BASE, status=200, key="refund-rule-baseline"):
    # gltest matches web mocks by the canonical base URL and strips query parameters.
    # Production still receives the per-operation cache key appended by the contract.
    payload = json.dumps({"type": "file", "encoding": "base64",
                          "content": base64.b64encode(body.encode()).decode()})
    vm.mock_web(URL, {"method": "GET", "status": status, "body": payload})


def verdict(vm, value):
    vm.mock_llm("DRIFT_LATCH_PRODUCER", json.dumps(json.dumps({"verdict": value})))


def create(vm, contract, owner):
    vm.sender = owner
    web(vm)
    contract.create_watch("refund-rule", "Refund policy watch", URL, 1, 1, RULE)
    vm.clear_mocks()


def test_fresh_snapshot_and_material_lifecycle(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy(CONTRACT)
    create(direct_vm, contract, direct_alice)
    web(direct_vm, key="same-one")
    assert contract.check_drift("refund-rule", "same-one") == "IDENTICAL"
    direct_vm.clear_mocks()
    web(direct_vm, CHANGED, key="deadline-cut")
    verdict(direct_vm, "MATERIAL")
    assert contract.check_drift("refund-rule", "deadline-cut") == "MATERIAL"
    check = contract.get_check("refund-rule", "deadline-cut")
    assert check["receipt"]["excerpt"].startswith("Refunds are available within 7 days.")
    assert check["receipt"]["sha256"] != contract.get_watch("refund-rule")["baseline"]["sha256"]
    watch = contract.get_watch("refund-rule")
    assert watch["state"] == "DRIFTED" and watch["baseline_version"] == 1
    direct_vm.clear_mocks()
    web(direct_vm, CHANGED, key="deadline-cut-adopt")
    contract.adopt_check("refund-rule", "deadline-cut")
    watch = contract.get_watch("refund-rule")
    assert watch["state"] == "MONITORED" and watch["baseline_version"] == 2
    assert contract.get_check("refund-rule", "deadline-cut")["adopted"] is True


def test_outside_window_is_bounded_without_llm(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy(CONTRACT)
    create(direct_vm, contract, direct_alice)
    web(direct_vm, BASE + "\nA new unrelated appendix.", key="appendix-only")
    assert contract.check_drift("refund-rule", "appendix-only") == "OUTSIDE_WINDOW"
    assert contract.get_watch("refund-rule")["state"] == "MONITORED"


def test_explicit_unavailable_receipt(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy(CONTRACT)
    create(direct_vm, contract, direct_alice)
    web(direct_vm, "missing", 404, key="source-down")
    assert contract.check_drift("refund-rule", "source-down") == "UNAVAILABLE"
    check = contract.get_check("refund-rule", "source-down")
    assert check["receipt"]["availability"] == "HTTP_ERROR"
    assert contract.get_watch("refund-rule")["state"] == "MONITORED"


def test_bad_source_and_unavailable_baseline_fail_closed(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    with direct_vm.expect_revert("GitHub Contents API"):
        contract.create_watch("bad-host", "Bad host", "https://api.github.com.evil.test/repos/acme/policy/contents/rules.txt", 1, 1, RULE)
    with direct_vm.expect_revert("GitHub Contents API"):
        contract.create_watch("caller-query", "Caller query", URL + "?ref=main", 1, 1, RULE)
    web(direct_vm, "missing", 503, key="source-down-baseline")
    with direct_vm.expect_revert("Baseline source is unavailable"):
        contract.create_watch("source-down", "Unavailable baseline", URL, 1, 1, RULE)


def test_owner_latest_and_replay_guards(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    create(direct_vm, contract, direct_alice)
    web(direct_vm, CHANGED, key="wording-one")
    verdict(direct_vm, "EDITORIAL")
    contract.check_drift("refund-rule", "wording-one")
    direct_vm.clear_mocks()
    web(direct_vm, CHANGED, key="wording-one")
    with direct_vm.expect_revert("Check ID already exists"):
        contract.check_drift("refund-rule", "wording-one")
    direct_vm.clear_mocks()
    direct_vm.sender = direct_bob
    web(direct_vm, CHANGED, key="wording-one-adopt")
    with direct_vm.expect_revert("Only owner"):
        contract.adopt_check("refund-rule", "wording-one")
    direct_vm.clear_mocks()
    direct_vm.sender = direct_alice
    web(direct_vm, key="same-two")
    contract.check_drift("refund-rule", "same-two")
    direct_vm.clear_mocks()
    with direct_vm.expect_revert("latest check"):
        contract.adopt_check("refund-rule", "wording-one")


def test_strict_fetch_validator_rejects_changed_snapshot(direct_vm, direct_deploy, direct_alice, monkeypatch):
    contract = direct_deploy(CONTRACT)
    gl = importlib.import_module("genlayer")
    direct_vm.sender = direct_alice
    web(direct_vm)
    contract.create_watch("refund-rule", "Refund policy watch", URL, 1, 1, RULE)
    direct_vm.clear_mocks()
    web(direct_vm, CHANGED, key="refund-rule-baseline")
    monkeypatch.setattr(gl.vm, "spawn_sandbox", lambda fn: gl.vm.Return(fn()))
    assert direct_vm.run_validator() is False


def test_semantic_validator_rejects_forged_editorial_result(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy(CONTRACT)
    create(direct_vm, contract, direct_alice)
    web(direct_vm, CHANGED, key="forged-editorial")
    verdict(direct_vm, "EDITORIAL")
    contract.check_drift("refund-rule", "forged-editorial")
    direct_vm.clear_mocks()
    web(direct_vm, CHANGED, key="forged-editorial")
    verdict(direct_vm, "MATERIAL")
    direct_vm._gl_call_hook = lambda _vm, request: {"ok": False} if "ExecPromptTemplate" in request else None
    assert direct_vm.run_validator() is False
    direct_vm._gl_call_hook = None


def test_archive_is_terminal(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    create(direct_vm, contract, direct_alice)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Only owner"):
        contract.archive_watch("refund-rule")
    direct_vm.sender = direct_alice
    contract.archive_watch("refund-rule")
    web(direct_vm, key="after-archive")
    with direct_vm.expect_revert("Archived watch"):
        contract.check_drift("refund-rule", "after-archive")
