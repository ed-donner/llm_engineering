"""TECH_ANALYST agent: technical indicators and signal scoring."""
from typing import List

from agents.base import AgentBase
from models import AssetData, TechResult


def _rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    import pandas as pd
    s = pd.Series(closes)
    delta = s.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0


def _ema(series: List[float], period: int) -> List[float]:
    if not series:
        return []
    import pandas as pd
    s = pd.Series(series)
    ema = s.ewm(span=period, adjust=False).mean()
    return ema.tolist()


def _macd_signal(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> str:
    if len(closes) < slow + signal:
        return "NEUTRAL"
    ema_f = _ema(closes, fast)
    ema_s = _ema(closes, slow)
    macd_line = [ema_f[i] - ema_s[i] for i in range(len(ema_f))]
    if len(macd_line) < signal:
        return "NEUTRAL"
    signal_line = _ema(macd_line, signal)
    if len(signal_line) < 2:
        return "NEUTRAL"
    if macd_line[-1] > signal_line[-1] and macd_line[-2] <= signal_line[-2]:
        return "BULLISH_CROSS"
    if macd_line[-1] < signal_line[-1] and macd_line[-2] >= signal_line[-2]:
        return "BEARISH_CROSS"
    return "NEUTRAL"


def _bb_signal(closes: List[float], period: int = 20, k: float = 2.0) -> str:
    if len(closes) < period:
        return "NEUTRAL"
    import pandas as pd
    s = pd.Series(closes)
    ma = s.rolling(period).mean().iloc[-1]
    std = s.rolling(period).std().iloc[-1]
    if pd.isna(std) or std == 0:
        return "NEUTRAL"
    upper = ma + k * std
    lower = ma - k * std
    price = closes[-1]
    if price <= lower:
        return "LOWER_BAND_BOUNCE"
    if price >= upper:
        return "UPPER_BAND_TOUCH"
    return "NEUTRAL"


def _ema_cross(closes: List[float], fast: int = 9, slow: int = 21) -> str:
    if len(closes) < slow + 1:
        return "NEUTRAL"
    ema_f = _ema(closes, fast)
    ema_s = _ema(closes, slow)
    if ema_f[-1] > ema_s[-1] and ema_f[-2] <= ema_s[-2]:
        return "GOLDEN_CROSS"
    if ema_f[-1] < ema_s[-1] and ema_f[-2] >= ema_s[-2]:
        return "DEATH_CROSS"
    return "NEUTRAL"


class TechAnalystAgent(AgentBase):
    name = "TECH_ANALYST"
    logger_name = "aria.tech_analyst"

    def run(self, assets: List[AssetData]) -> List[TechResult]:
        self.log("Running technical analysis")
        results: List[TechResult] = []
        for a in assets:
            closes = [c["c"] for c in (a.ohlcv_50 or a.ohlcv_14) if isinstance(c, dict) and "c" in c]
            if not closes:
                closes = [a.price]
            rsi = _rsi(closes)
            macd_signal = _macd_signal(closes)
            bb_signal = _bb_signal(closes)
            ema_cross = _ema_cross(closes)
            volume_spike = a.volume_ratio > 1.5
            score = 0
            # Bullish
            if rsi < 30:
                score += 20
            elif rsi > 70:
                score -= 20
            if macd_signal == "BULLISH_CROSS":
                score += 25
            elif macd_signal == "BEARISH_CROSS":
                score -= 25
            if bb_signal == "LOWER_BAND_BOUNCE":
                score += 20
            elif bb_signal == "UPPER_BAND_TOUCH":
                score -= 20
            if ema_cross == "GOLDEN_CROSS":
                score += 25
            elif ema_cross == "DEATH_CROSS":
                score -= 25
            if volume_spike:
                score += 10
            if a.high_52w and a.price >= a.high_52w * 0.97:
                score += 10
            elif a.low_52w and a.price <= a.low_52w * 1.05:
                score += 15
            score = max(-100, min(100, score))
            if score >= 50:
                bias = "STRONG BUY"
            elif score >= 20:
                bias = "MODERATE BUY"
            elif score <= -50:
                bias = "STRONG SELL"
            elif score <= -20:
                bias = "MODERATE SELL"
            else:
                bias = "NEUTRAL"
            results.append(TechResult(
                asset=a.asset,
                rsi=round(rsi, 1),
                macd_signal=macd_signal,
                bb_signal=bb_signal,
                ema_cross=ema_cross,
                volume_spike=volume_spike,
                tech_score=score,
                bias=bias,
            ))
            self.log(f"{a.asset}: score={score} bias={bias}")
        self.log(f"Tech analysis complete: {len(results)} assets")
        return results
