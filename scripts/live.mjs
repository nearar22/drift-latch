import { createAccount, createClient, isSuccessful } from "genlayer-js";
import { studioDevnet } from "genlayer-js/chains";

const rawKey = process.env.GENLAYER_PRIVATE_KEY?.trim();
const contract = process.env.CONTRACT_ADDRESS?.trim();
const stage = process.env.LIVE_STAGE?.trim();
if (!rawKey || !contract || !["baseline", "check", "adopt", "inspect"].includes(stage)) {
  throw new Error("GENLAYER_PRIVATE_KEY, CONTRACT_ADDRESS, and LIVE_STAGE=baseline|check|adopt|inspect are required");
}
const key = rawKey.startsWith("0x") ? rawKey : `0x${rawKey}`;
const chain = { ...studioDevnet, id: 61997, name: "GenLayer Studio Next", rpcUrls: { default: { http: ["https://studio-next.genlayer.com/api"] } } };
const client = createClient({ chain, account: createAccount(key) });
const source = "https://drift-latch-feed.driftglass-cov.pages.dev/refund-policy.txt";
const watchId = "refund-policy";
const checkId = process.env.LIVE_CHECK_ID?.trim() || "deadline-cut";

async function write(label, method, args, intelligent = false) {
  const fees = await client.estimateTransactionFees({ leaderTimeunitsAllocation: intelligent ? 300n : 125n, validatorTimeunitsAllocation: intelligent ? 600n : 250n });
  const hash = await client.writeContract({ address: contract, functionName: method, args, fees });
  console.log(`${label}_TX=${hash}`);
  const receipt = await client.waitForTransactionReceipt({ hash, waitUntil: "finalized", retries: 240, interval: 3000, fullTransaction: true });
  const status = String(receipt.statusName ?? receipt.status ?? "unknown");
  const execution = String(receipt.txExecutionResultName ?? receipt.txExecutionResult ?? "unknown");
  console.log(`${label}_STATUS=${status};EXECUTION_RESULT=${execution}`);
  if (!isSuccessful(receipt) || status !== "FINALIZED" || execution !== "FINISHED_WITH_RETURN") throw new Error(`${label} did not finalize successfully`);
  return hash;
}

if (stage === "baseline") {
  await write("BASELINE", "create_watch", [watchId, "Refund deadline tripwire", source, 1, 1,
    "Any change to the refund deadline, eligibility, exclusions, or required customer steps is material."], true);
} else if (stage === "check") {
  await write("CHECK", "check_drift", [watchId, checkId], true);
} else if (stage === "adopt") {
  await write("ADOPT", "adopt_check", [watchId, checkId], true);
}

const watch = await client.readContract({ address: contract, functionName: "get_watch", args: [watchId], jsonSafeReturn: true });
console.log(`WATCH_STATE=${JSON.stringify(watch)}`);
if (stage === "baseline" && (watch.state !== "MONITORED" || watch.baseline_version !== 1)) throw new Error("Unexpected baseline state");
if (stage === "check" && watch.state !== "DRIFTED") throw new Error("Material change did not latch");
if (stage === "adopt" && (watch.state !== "MONITORED" || watch.baseline_version !== 2)) throw new Error("Adoption did not rearm watch");
if (watch.check_ids.includes(checkId)) {
  const check = await client.readContract({ address: contract, functionName: "get_check", args: [watchId, checkId], jsonSafeReturn: true });
  console.log(`CHECK_STATE=${JSON.stringify(check)}`);
}
