"""ARC: Zeilen- und Funktionsabdeckung der bestehenden 105 Tests (stdlib `trace`, kein Zusatzpaket).
numba-Funktionen (@njit) laufen kompiliert und sind fuer `trace` unsichtbar; sie werden getrennt ausgewiesen.
Aufruf aus swing-hybrid: .venv/bin/python -I -B <skript> <ausgabe.json>
"""
import ast, json, sys, trace
from pathlib import Path
ROOT = Path.cwd()
ZIELE = sorted(list((ROOT / "src/hybrid").glob("*.py")) + list((ROOT / "vorwaertstest").glob("*.py")) + [ROOT / "scripts/vorwaertstest_auswerten.py"])
import pytest
tr = trace.Trace(count=1, trace=0, ignoredirs=[sys.prefix, sys.exec_prefix, str(ROOT / ".venv")])
rc = tr.runfunc(pytest.main, ["-q", "-p", "no:cacheprovider", "tests"])
counts = tr.results().counts
getroffen = {}
for (fn, ln), n in counts.items():
    getroffen.setdefault(str(Path(fn).resolve()), set()).add(ln)
out, zeilen = {}, []
for p in ZIELE:
    src = p.read_text()
    baum = ast.parse(src)
    ausfuehrbar = {l for l in trace._find_executable_linenos(str(p)) if l is not None}
    hit = getroffen.get(str(p.resolve()), set())
    funcs = []
    for n in ast.walk(baum):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            jit = any("njit" in ast.unparse(d) for d in n.decorator_list)
            zl = {l for l in ausfuehrbar if n.lineno < l <= n.end_lineno}
            funcs.append({"name": n.name, "zeile": n.lineno, "njit": jit, "ausfuehrbar": len(zl), "getroffen": len(zl & hit)})
    ges = len(ausfuehrbar); g = len(ausfuehrbar & hit)
    rel = str(p.relative_to(ROOT))
    out[rel] = {"ausfuehrbar": ges, "getroffen": g, "funktionen": funcs}
    nie = [f"{f['name']}:{f['zeile']}" for f in funcs if not f["njit"] and f["ausfuehrbar"] and f["getroffen"] == 0]
    teil = [f"{f['name']}:{f['zeile']} ({f['getroffen']}/{f['ausfuehrbar']})" for f in funcs if not f["njit"] and 0 < f["getroffen"] < f["ausfuehrbar"]]
    jit = [f["name"] for f in funcs if f["njit"]]
    zeilen.append((rel, ges, g, nie, teil, jit))
print(f"pytest-Rueckgabe: {rc}")
print(f"{'Datei':42s} {'Zeilen':>6s} {'getr.':>6s} {'%':>5s}")
for rel, ges, g, nie, teil, jit in zeilen:
    print(f"{rel:42s} {ges:6d} {g:6d} {100*g/max(ges,1):5.0f}")
print()
for rel, ges, g, nie, teil, jit in zeilen:
    if nie: print(f"{rel}: von keinem Test ausgefuehrt: {', '.join(nie)}")
    if teil: print(f"{rel}: teilweise: {', '.join(teil)}")
    if jit: print(f"{rel}: @njit (fuer trace unsichtbar): {', '.join(jit)}")
json.dump(out, open(sys.argv[1], "w"), indent=1)
