import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { authenticate, createSession } from "@/server/auth/sessions";
import { SESSION_COOKIE } from "@/server/auth/current";
import { audit } from "@/server/audit";
import { env } from "@/server/env";
import { Field, inputCls } from "@/components/ui";

async function login(formData: FormData) {
  "use server";
  const email = String(formData.get("email") ?? "");
  const password = String(formData.get("password") ?? "");
  const user = await authenticate(email, password);
  if (!user) {
    await audit({ id: null, label: email.slice(0, 100) || "unknown" }, "auth.login_failed", "user", null);
    redirect("/login?err=1");
  }
  const { token, expiresAt } = await createSession(user.id);
  (await cookies()).set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: env().APP_URL.startsWith("https://"),
    path: "/",
    expires: expiresAt,
  });
  await audit({ id: user.id, label: user.email }, "auth.login", "user", user.id);
  redirect("/");
}

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ err?: string }> }) {
  const { err } = await searchParams;
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <form action={login} className="w-full max-w-sm space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <h1 className="text-xl font-semibold">Content Engine</h1>
          <p className="text-sm text-slate-500">Anmeldung für das Team</p>
        </div>
        {err ? <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">E-Mail oder Passwort falsch.</p> : null}
        <Field label="E-Mail">
          <input name="email" type="email" required autoComplete="username" className={inputCls} />
        </Field>
        <Field label="Passwort">
          <input name="password" type="password" required autoComplete="current-password" className={inputCls} />
        </Field>
        <button type="submit" className="w-full rounded-lg bg-slate-900 py-2 text-sm font-medium text-white hover:bg-slate-700">
          Anmelden
        </button>
      </form>
    </main>
  );
}
