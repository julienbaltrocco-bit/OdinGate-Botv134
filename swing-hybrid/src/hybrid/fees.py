"""Yubit-Futures-Gebühren. Gebühr = Satz x volles Positionsvolumen (Nominalwert, inkl. Hebel), je Seite."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Fees:
    maker: float = 0.0004
    taker: float = 0.0008
    rebate: float = 0.0  # Anteil der Gebühr, der zurückkommt (0.85 = 85 %)

    def rate(self, kind: str) -> float:
        if kind not in ("maker", "taker"):
            raise ValueError(kind)
        return getattr(self, kind)

    def gross(self, notional: float, kind: str) -> float:
        """Gebühr, die die Börse zunächst abzieht."""
        return abs(notional) * self.rate(kind)

    def net(self, notional: float, kind: str) -> float:
        """Gebühr nach Rebate (effektiv)."""
        return self.gross(notional, kind) * (1.0 - self.rebate)

    def rebate_amount(self, notional: float, kind: str) -> float:
        return self.gross(notional, kind) * self.rebate


def scenarios(cfg: dict) -> dict[str, Fees]:
    g = cfg["gebuehren"]
    return {
        "mit_rebate": Fees(g["maker"], g["taker"], g["rebate_anteil"]),
        "ohne_rebate": Fees(g["maker"], g["taker"], 0.0),
    }
