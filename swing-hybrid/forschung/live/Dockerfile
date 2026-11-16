# Abgeschlossene Umgebung für den OdinGate-Live-Papierhandel (nur Simulation). Der Code kommt als eingebundener Ordner /repo.
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends git openssh-client openssl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir numpy==2.5.4 pandas==3.1.1 numba==0.68.1
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 ODINGATE_DATEN=/daten NUMBA_CACHE_DIR=/daten/numba
WORKDIR /repo/swing-hybrid
CMD ["python", "-m", "forschung.live.dienst", "L-dc1d27a3"]
