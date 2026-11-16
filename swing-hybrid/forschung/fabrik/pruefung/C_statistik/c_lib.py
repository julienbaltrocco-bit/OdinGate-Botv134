"""Hilfen für den Prüfbereich C: echte trichter.statistik() auf einer KÜNSTLICHEN Datenbank ausführen (alles unter C_statistik/tmp),
und eine eigene, unabhängige Nachrechnung von Reality Check und PBO."""
import contextlib, io, itertools, math, os, sqlite3, sys
from pathlib import Path
import numpy as np
os.environ.setdefault("OMP_NUM_THREADS", "2"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
sys.path.insert(0, 'forschung')
from fabrik import daten as D, lauf as L, trichter as T

HIER = Path(__file__).resolve().parent
TMP = HIER / "tmp"
ECHT_DB, ECHT_SPEICHER, ECHT_ERG = L.DB, D.SPEICHER, T.ERG
ECHT_AUS = Path('data/fabrik')                     # Lauf A (Datenbank und Tagesreihen); seit 00:14 UTC liest trichter die Tagesreihen aus L.AUS (Umgebungsvariable FABRIK_AUS)
RO = 'file:data/fabrik/forschung.sqlite?mode=ro'


def stand():
    """Prüfsummen des geprüften Codes (er wurde während der Prüfung um 00:05:59 UTC von anderer Stelle geändert)."""
    import hashlib
    return " ".join(f"{n}:{hashlib.sha1((HIER.parents[1] / (n + '.py')).read_bytes()).hexdigest()[:8]}" for n in ("trichter", "lauf", "kern", "evolution"))


def ro():
    con = sqlite3.connect(RO, uri=True)
    con.row_factory = sqlite3.Row
    return con


def kuenstliche_welt(n, braucht="k", name="syn"):
    """Legt unter tmp/ eine Datenbank mit n gültigen Kandidaten an und biegt die Pfade der Fabrik IN DIESEM PROZESS dorthin um."""
    TMP.mkdir(exist_ok=True)
    pfad = TMP / f"{name}.sqlite"
    if pfad.exists():
        pfad.unlink()
    con = sqlite3.connect(pfad)
    con.execute(f"CREATE TABLE kandidaten ({', '.join(L.SPALTEN)}, PRIMARY KEY (id, gen))")
    sp = {s: None for s in L.SPALTEN}
    zeilen = []
    for i in range(n):
        z = dict(sp, id=f"k{i}", gen="syn", signal="mom_12", familie="Momentum", braucht=braucht, th=1.5, r=1, f="kein", k=1, x="h60", m="top3", zeile=i,
                 n_t=500, t_roh_t=0.0, t85_t=0.0, sharpe_t=0.0, status="verworfen_1", grund="")
        zeilen.append(tuple(z[s] for s in L.SPALTEN))
    con.executemany(f"INSERT INTO kandidaten VALUES ({','.join('?' * len(L.SPALTEN))})", zeilen)
    con.commit(); con.close()
    L.DB, L.AUS, T.ERG = pfad, TMP, TMP
    assert str(TMP) in str(L.DB) and str(TMP) in str(T.ERG) and str(TMP) in str(L.AUS)


def echte_statistik(X):
    """X: [n, N_TAGE] Tagesergebnisse. Schreibt sie als tage_syn.npy nach tmp/ und ruft die ECHTE Funktion trichter.statistik() auf."""
    assert str(TMP) in str(L.DB) and str(TMP) in str(T.ERG) and str(TMP) in str(L.AUS), "Pfade nicht umgebogen"
    np.save(TMP / "tage_syn.npy", X.astype(np.float32))
    with contextlib.redirect_stdout(io.StringIO()):
        aus = T.statistik()
    return list(aus["gruppen"].values())[0]


def gewichte(tage, B, block, rng):
    """Stationärer Bootstrap (Politis/Romano), kreisförmig: Rückgabe Indexfelder [B, tage]."""
    alle = np.empty((B, tage), np.int64)
    for b in range(B):
        neu = rng.random(tage) < 1.0 / block
        starts = rng.integers(0, tage, tage)
        pos = 0
        for i in range(tage):
            pos = starts[i] if (neu[i] or i == 0) else (pos + 1) % tage
            alle[b, i] = pos
    return alle


def rc_eigen(t, idx, selbst=False):
    """Eigene Nachrechnung des Reality Check mit ausdrücklichem Ziehen der Tage (keine Gewichtsmatrix).
    t: [n, tage] (float64). idx: [B, tage]. selbst=True: jede Bootstrap-Stichprobe wird durch IHRE EIGENE Streuung geteilt
    (so ist die Prüfgröße der echten Daten gebildet); selbst=False: feste Streuung der Originalreihe (so rechnet trichter.statistik)."""
    t = np.asarray(t, np.float64)
    tage = t.shape[1]
    mu, sd = t.mean(1), t.std(1, ddof=1)
    ok = sd > 0
    tw = np.where(ok, mu / np.where(ok, sd, 1) * math.sqrt(tage), 0)
    maxima = np.empty(len(idx))
    for b, ix in enumerate(idx):
        s = t[:, ix]
        mb = s.mean(1)
        if selbst:
            sb = s.std(1, ddof=1)
            g = ok & (sb > 0)
            st = np.where(g, (mb - mu) / np.where(g, sb, 1) * math.sqrt(tage), -np.inf)
        else:
            st = np.where(ok, (mb - mu) / np.where(ok, sd, 1) * math.sqrt(tage), -np.inf)
        maxima[b] = st.max()
    return float(tw.max()), float((maxima >= tw.max()).mean()), maxima


def rc_gewichte(t, idx, selbst=False):
    """Dieselbe Rechnung über Gewichte (schnell, für viele Wiederholungen). selbst=True braucht zusätzlich die zweiten Momente."""
    t = np.asarray(t, np.float64)
    n, tage = t.shape
    W = np.stack([np.bincount(ix, minlength=tage) for ix in idx]).astype(np.float64) / tage
    mu, sd = t.mean(1), t.std(1, ddof=1)
    ok = sd > 0
    tw = np.where(ok, mu / np.where(ok, sd, 1) * math.sqrt(tage), 0)
    mb = t @ W.T
    if selbst:
        qb = (t * t) @ W.T
        vb = np.maximum(qb - mb ** 2, 0) * tage / (tage - 1)
        g = ok[:, None] & (vb > 0)
        st = np.where(g, (mb - mu[:, None]) / np.sqrt(np.where(g, vb, 1)) * math.sqrt(tage), -np.inf)
    else:
        st = np.where(ok[:, None], (mb - mu[:, None]) / np.where(ok, sd, 1)[:, None] * math.sqrt(tage), -np.inf)
    maxima = st.max(0)
    return float(tw.max()), float((maxima >= tw.max()).mean()), maxima


def pbo_eigen(m, e0, e1, K=10):
    """Eigene Nachrechnung der PBO (CSCV nach Bailey u. a.): Sharpe je Hälfte direkt aus den Tageswerten, nicht aus Blocksummen."""
    m = np.asarray(m, np.float64)
    grenzen = np.linspace(e0, e1, K + 1).astype(int)
    bloecke = [np.arange(grenzen[i], grenzen[i + 1]) for i in range(K)]
    unter, verliert, n = 0, 0, 0
    for kombi in itertools.combinations(range(K), K // 2):
        a = np.concatenate([bloecke[i] for i in kombi])
        b = np.concatenate([bloecke[i] for i in range(K) if i not in kombi])
        def sh(tage):
            x = m[:, tage]
            s = x.std(1)
            return np.where(s > 0, x.mean(1) / np.where(s > 0, s, 1), -np.inf)
        sis, soos = sh(a), sh(b)
        k = int(sis.argmax())
        rang = (soos < soos[k]).sum() / len(soos)
        rang = min(max(rang, 1 / (len(soos) + 1)), 1 - 1 / (len(soos) + 1))
        unter += math.log(rang / (1 - rang)) <= 0
        verliert += soos[k] <= 0
        n += 1
    return unter / n, verliert / n, n


def blind():
    """V2-blinde Umgebung für diesen Prozess: alle Speicher werden bei I_ENDE (2024-07-01) abgeschnitten, D.N = I_ENDE.
    Jeder Zugriff auf eine Kerze ab 2024-07-01 liefe damit ins Leere (IndexError) - es wird nachweislich nichts aus V2 gelesen."""
    ende = L.I_ENDE
    echt = D.laden
    def laden(name):
        a = echt(name)
        return a if name == "slip_bp" else a[..., :ende]
    D.laden = laden
    D.N = ende
    L._g.clear(); L._init()
    assert all(v.shape[-1] == ende for k, v in L._g.items() if k in ("o", "h", "l", "c", "fcum", "gueltig", "signale", "filter", "sigma", "handelbar"))
    return ende
