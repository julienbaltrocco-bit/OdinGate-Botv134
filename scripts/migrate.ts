import "dotenv/config";
import { migrate } from "drizzle-orm/node-postgres/migrator";
import { closeDb, db } from "@/server/db";


async function main() {
  await migrate(db(), { migrationsFolder: "./drizzle" });
  console.log("Migrationen angewendet.");
  await closeDb();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
