import "dotenv/config";
import { count } from "drizzle-orm";
import { closeDb, db, schema } from "@/server/db";
import { createUser } from "@/server/auth/users";
import { getBrand } from "@/server/brand";
import { SYSTEM_ACTOR } from "@/server/audit";

/**
 * Creates the first admin and the default brand profile.
 * Usage: pnpm seed -- --email you@example.com --name "Vorname Nachname" --password '...'
 * (or ADMIN_EMAIL / ADMIN_NAME / ADMIN_PASSWORD env vars).
 */
function arg(name: string) {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 ? process.argv[i + 1] : undefined;
}

async function main() {
  await getBrand();
  const [{ value: users }] = await db().select({ value: count() }).from(schema.users);
  if (users === 0) {
    const email = arg("email") ?? process.env.ADMIN_EMAIL;
    const password = arg("password") ?? process.env.ADMIN_PASSWORD;
    const name = arg("name") ?? process.env.ADMIN_NAME ?? "Admin";
    if (!email || !password) {
      console.error("Kein Benutzer vorhanden. Bitte --email und --password (min. 12 Zeichen) angeben.");
      process.exit(1);
    }
    await createUser(SYSTEM_ACTOR, { email, name, role: "admin", password });
    console.log(`Admin ${email} angelegt.`);
  } else {
    console.log(`${users} Benutzer vorhanden – kein Admin angelegt.`);
  }
  console.log("Brand-Profil vorhanden.");
  await closeDb();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
