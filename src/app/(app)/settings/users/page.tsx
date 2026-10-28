import { asc } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { action, str } from "@/server/actions";
import { db, schema } from "@/server/db";
import { createUser, resetPassword, setUserActive, setUserRole } from "@/server/auth/users";
import { PERMISSIONS, ROLE_LABELS, type Role } from "@/server/auth/rbac";
import { Badge, Button, Card, Field, Flash, inputCls, PageHeader, Table } from "@/components/ui";

const ROLES = Object.keys(ROLE_LABELS) as Role[];

async function create(fd: FormData) {
  "use server";
  await action("/settings/users", "users.manage", async ({ actor }) => {
    await createUser(actor, { email: str(fd, "email"), name: str(fd, "name"), role: str(fd, "role") as Role, password: str(fd, "password") });
    return "Benutzer angelegt.";
  });
}

async function update(fd: FormData) {
  "use server";
  await action("/settings/users", "users.manage", async ({ actor }) => {
    const id = str(fd, "id");
    const op = str(fd, "op");
    if (op === "role") await setUserRole(actor, id, str(fd, "role") as Role);
    else if (op === "deactivate") await setUserActive(actor, id, false);
    else if (op === "activate") await setUserActive(actor, id, true);
    else if (op === "password") await resetPassword(actor, id, str(fd, "password"));
    return "Gespeichert.";
  });
}

export default async function UsersPage({ searchParams }: { searchParams: Promise<{ ok?: string; err?: string }> }) {
  await requireUser("users.manage");
  const sp = await searchParams;
  const users = await db().select().from(schema.users).orderBy(asc(schema.users.createdAt));
  return (
    <>
      <PageHeader title="Team & Rollen" />
      <Flash ok={sp.ok} err={sp.err} />
      <Card title="Benutzer" className="mb-6">
        <Table head={["Name", "E-Mail", "Rolle", "Status", "Passwort"]}>
          {users.map((u) => (
            <tr key={u.id}>
              <td className="px-2 py-2">{u.name}</td>
              <td className="px-2 py-2 text-xs">{u.email}</td>
              <td className="px-2 py-2">
                <form action={update} className="flex gap-1">
                  <input type="hidden" name="id" value={u.id} />
                  <input type="hidden" name="op" value="role" />
                  <select name="role" defaultValue={u.role} className={`${inputCls} w-auto py-1`}>{ROLES.map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}</select>
                  <Button variant="secondary">OK</Button>
                </form>
              </td>
              <td className="px-2 py-2">
                <form action={update} className="flex items-center gap-2">
                  <input type="hidden" name="id" value={u.id} />
                  <Badge color={u.active ? "green" : "slate"}>{u.active ? "aktiv" : "deaktiviert"}</Badge>
                  <Button variant="ghost" name="op" value={u.active ? "deactivate" : "activate"}>{u.active ? "Deaktivieren" : "Aktivieren"}</Button>
                </form>
              </td>
              <td className="px-2 py-2">
                <form action={update} className="flex gap-1">
                  <input type="hidden" name="id" value={u.id} />
                  <input type="hidden" name="op" value="password" />
                  <input name="password" type="password" minLength={12} placeholder="Neues Passwort" className={`${inputCls} w-40 py-1`} />
                  <Button variant="secondary">Setzen</Button>
                </form>
              </td>
            </tr>
          ))}
        </Table>
      </Card>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Benutzer anlegen">
          <form action={create} className="grid gap-3 md:grid-cols-2">
            <Field label="Name"><input name="name" required className={inputCls} /></Field>
            <Field label="E-Mail"><input name="email" type="email" required className={inputCls} /></Field>
            <Field label="Rolle"><select name="role" className={inputCls}>{ROLES.map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}</select></Field>
            <Field label="Startpasswort (min. 12 Zeichen)"><input name="password" type="password" minLength={12} required className={inputCls} /></Field>
            <div><Button>Anlegen</Button></div>
          </form>
        </Card>
        <Card title="Berechtigungsmatrix">
          <Table head={["Recht", ...ROLES.map((r) => ROLE_LABELS[r].split(" ")[0])]}>
            {Object.entries(PERMISSIONS).map(([p, roles]) => (
              <tr key={p}>
                <td className="px-2 py-1 font-mono text-xs">{p}</td>
                {ROLES.map((r) => <td key={r} className="px-2 py-1 text-center text-xs">{(roles as readonly Role[]).includes(r) ? "✓" : ""}</td>)}
              </tr>
            ))}
          </Table>
        </Card>
      </div>
    </>
  );
}
