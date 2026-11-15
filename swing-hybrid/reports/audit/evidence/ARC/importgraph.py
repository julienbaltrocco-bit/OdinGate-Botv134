"""Importgraph (statisch, per ast) fuer src/hybrid, scripts, vorwaertstest, tests. Nur lesend."""
import ast, sys, json
from pathlib import Path
ROOT = Path(sys.argv[1])
def imports(p):
    t = ast.parse(p.read_text())
    out = set()
    for n in ast.walk(t):
        if isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            if n.level and not mod:           # from . import a, b
                for a in n.names: out.add(("rel", a.name))
            elif n.level:
                out.add(("rel", mod.split(".")[0]))
            else:
                if mod.split(".")[0] in ("hybrid", "vorwaertstest"):
                    if mod in ("hybrid", "vorwaertstest"):
                        for a in n.names: out.add((mod, a.name))
                    else:
                        out.add((mod.split(".")[0], mod.split(".")[1]))
                else:
                    out.add(("ext", mod.split(".")[0]))
        elif isinstance(n, ast.Import):
            for a in n.names:
                top = a.name.split(".")
                if top[0] in ("hybrid", "vorwaertstest") and len(top) > 1:
                    out.add((top[0], top[1]))
                else:
                    out.add(("ext", top[0]))
    return out
res = {}
for grp, glob in (("hybrid", "src/hybrid/*.py"), ("scripts", "scripts/*.py"), ("vorwaertstest", "vorwaertstest/*.py"), ("tests", "tests/*.py")):
    for p in sorted(ROOT.glob(glob)):
        im = imports(p)
        intern = sorted({(grp if k == "rel" else k) + "." + v for k, v in im if k != "ext"})
        ext = sorted({v for k, v in im if k == "ext"})
        res[f"{grp}/{p.stem}"] = {"intern": intern, "extern": ext}
print("== Interne Abhaengigkeiten ==")
for k, v in res.items():
    print(f"{k:38s} -> {', '.join(v['intern']) or '-'}")
print()
print("== Externe Pakete je Gruppe ==")
import collections
g = collections.defaultdict(set)
for k, v in res.items():
    g[k.split('/')[0]].update(v["extern"])
STD = set(sys.stdlib_module_names)
for k, v in g.items():
    print(k, "| Drittanbieter:", sorted(x for x in v if x not in STD), "| Standardbibliothek:", sorted(x for x in v if x in STD))
print()
print("== Wer nutzt welches hybrid-Modul (eingehende Kanten) ==")
inc = collections.defaultdict(list)
for k, v in res.items():
    for i in v["intern"]:
        inc[i].append(k)
for mod in sorted(inc):
    print(f"{mod:32s} <- {len(inc[mod]):2d}: {', '.join(inc[mod])}")
alle = {f"hybrid.{p.stem}" for p in ROOT.glob('src/hybrid/*.py') if p.stem != '__init__'}
print()
print("hybrid-Module ohne eingehende Kante aus scripts/hybrid/vorwaertstest (nur Tests oder niemand):")
for mod in sorted(alle):
    nutzer = [u for u in inc.get(mod, []) if not u.startswith("tests/")]
    if not nutzer:
        print("  ", mod, "| Tests:", [u for u in inc.get(mod, [])])
json.dump(res, open(sys.argv[2], "w"), indent=1)
