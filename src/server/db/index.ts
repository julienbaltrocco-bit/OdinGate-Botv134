import { drizzle, type NodePgDatabase } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import { env } from "@/server/env";
import * as schema from "./schema";

export type DB = NodePgDatabase<typeof schema>;

const globalForDb = globalThis as unknown as { __pool?: Pool; __db?: DB };

export function getPool(): Pool {
  if (!globalForDb.__pool) {
    globalForDb.__pool = new Pool({ connectionString: env().DATABASE_URL, max: 10 });
  }
  return globalForDb.__pool;
}

export function db(): DB {
  if (!globalForDb.__db) {
    globalForDb.__db = drizzle(getPool(), { schema });
  }
  return globalForDb.__db;
}

export async function closeDb() {
  await globalForDb.__pool?.end();
  globalForDb.__pool = undefined;
  globalForDb.__db = undefined;
}

export { schema };
