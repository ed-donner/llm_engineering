"""
Pydantic models for ARIA pipeline: asset data, tech result, sentiment, decision, alert payload.
"""
from typing import Optional
from pydantic import BaseModel, Field


class AssetData(BaseModel):
    asset: str
    price: float
    change_1h: str = ""
    change_24h: str = ""
    volume_ratio: float = 1.0
    ohlcv_14: list[dict] = Field(default_factory=list)  # e.g. [{"o", "h", "l", "c", "v", "t"}, ...]
    ohlcv_50: list[dict] = Field(default_factory=list)
    high_52w: float = 0.0
    low_52w: float = 0.0


class TechResult(BaseModel):
    asset: str
    rsi: float = 0.0
    macd_signal: str = "NEUTRAL"  # BULLISH_CROSS, BEARISH_CROSS, NEUTRAL
    bb_signal: str = "NEUTRAL"   # LOWER_BAND_BOUNCE, UPPER_BAND_TOUCH, NEUTRAL
    ema_cross: str = "NEUTRAL"   # GOLDEN_CROSS, DEATH_CROSS, NEUTRAL
    volume_spike: bool = False
    tech_score: int = 0
    bias: str = "NEUTRAL"  # STRONG BUY, MODERATE BUY, NEUTRAL, MODERATE SELL, STRONG SELL


class SentimentResult(BaseModel):
    asset: str
    headlines: list[str] = Field(default_factory=list)
    sentiment: str = "MIXED"  # POSITIVE, NEGATIVE, MIXED
    sentiment_score: int = 0   # +1, 0, -1
    narrative: str = ""


class DecisionRecord(BaseModel):
    asset: str
    tech_score: int = 0
    sentiment: str = "MIXED"
    final_score: float = 0.0
    decision: str = "SKIP"  # ALERT | SKIP
    priority: int = 0
    skip_reason: Optional[str] = None


class AlertPayload(BaseModel):
    asset: str
    bias: str
    price: float
    change_24h: str
    tech_score: int
    sentiment: str
    narrative: str
    final_score: float
    key_signals: list[str] = Field(default_factory=list)
    url: str = ""
