"""ARC: nicht ausgefuehrte Zeilen in den Betriebsdateien des Papier-Bots (aus demselben trace-Lauf wie abdeckung.py)."""
import sys, trace
from pathlib import Path
ROOT = Path.cwd()
import pytest
tr = trace.Trace(count=1, trace=0, ignoredirs=[sys.prefix, sys.exec_prefix, str(ROOT / ".venv")])
tr.runfunc(pytest.main, ["-q", "-p", "no:cacheprovider", "tests"])
hit = {}
for (fn, ln), n in tr.results().counts.items():
    hit.setdefault(str(Path(fn).resolve()), set()).add(ln)
for rel in ("vorwaertstest/bot.py", "vorwaertstest/kern.py", "vorwaertstest/yubit.py", "vorwaertstest/dashboard_daten.py"):
    p = ROOT / rel
    ex = sorted(l for l in trace._find_executable_linenos(str(p)) if l is not None)
    fehlt = [l for l in ex if l not in hit.get(str(p.resolve()), set())]
    src = p.read_text().splitlines()
    print(f"== {rel}: {len(fehlt)} von {len(ex)} ausfuehrbaren Zeilen nie ausgefuehrt")
    for l in fehlt:
        print(f"  {l:4d}: {src[l-1].strip()[:150]}")
