import "dotenv/config";
import { runWorker } from "@/server/jobs/worker";
import { env } from "@/server/env";

env(); // fail fast on invalid configuration
console.log("[worker] gestartet");
runWorker().then(() => {
  console.log("[worker] beendet");
  process.exit(0);
});
