import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { createClient } from "genlayer-js";
import { studioDevnet } from "genlayer-js/chains";

const address = "0xAD8a4605A8382C6A6fA9487c8f30C822892cC571";
const hashes = {
  deploy: "0xc8e0d776291089dc0dd794acbe0664031171f3ed4b91a215793da0ec3403a62f",
  baseline: "0xca686ea9dba72898c30f54d53ee324eb3c0bb624fdc6cd81934dd2f9922c203d",
  check: "0xe750d6e085c789b780a4abcd50c71ead5c0f99d4fa650078ce64aa6f03f6ec3d",
  adopt: "0x928d961ffbc0d001c4c1cefb7f8b95143075929b19322ff3846d6562ca7c1644",
};
const chain = { ...studioDevnet, id: 61997, name: "GenLayer Studio Next", rpcUrls: { default: { http: ["https://studio-next.genlayer.com/api"] } } };
const client = createClient({ chain });
const local = readFileSync(new URL("../contracts/drift_latch.py", import.meta.url), "utf8");
const deployed = await client.getContractCode(address);
const sha256 = (text) => createHash("sha256").update(text, "utf8").digest("hex");
console.log(`LOCAL_SHA256=${sha256(local)}`);
console.log(`DEPLOYED_SHA256=${sha256(deployed)}`);
console.log(`SOURCE_MATCH=${local === deployed}`);
if (local !== deployed) throw new Error("Deployed source does not match repository source");
for (const [label, hash] of Object.entries(hashes)) {
  const tx = await client.getTransaction({ hash });
  const status = String(tx.statusName ?? tx.status ?? "unknown");
  const execution = String(tx.txExecutionResultName ?? tx.txExecutionResult ?? "unknown");
  console.log(`${label.toUpperCase()}=${status};EXECUTION_RESULT=${execution}`);
  if (status !== "FINALIZED" || execution !== "FINISHED_WITH_RETURN") throw new Error(`${label} transaction is not finalized and successful`);
}
