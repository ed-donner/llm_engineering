"""DECISION_AGENT: combine tech + sentiment, apply alert rules."""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from agents.base import AgentBase
from models import TechResult, SentimentResult, DecisionRecord, AssetData

from config import (
    ALERT_SCORE_THRESHOLD,
    MAX_ALERTS_PER_HOUR,
    ASSET_COOLDOWN_HOURS,
    SCORE_BUMP_TO_OVERRIDE_COOLDOWN,
    ASSETS_24_7,
    MARKET_OPEN_HOUR_ET,
    MARKET_CLOSE_HOUR_ET,
)


def _is_market_hours_et() -> bool:
    # Simple check: use ET (UTC-5 or UTC-4). For robustness use zoneinfo in Py3.9+
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        now = datetime.now(timezone.utc)
        # Approximate ET = UTC-5
        now = now.replace(tzinfo=timezone.utc) - timedelta(hours=5)
    if now.weekday() >= 5:  # Sat=5, Sun=6
        return False
    return MARKET_OPEN_HOUR_ET <= now.hour < MARKET_CLOSE_HOUR_ET


class DecisionAgent(AgentBase):
    name = "DECISION_AGENT"
    logger_name = "aria.decision_agent"

    def __init__(self):
        super().__init__()
        self._last_alert_per_asset: Dict[str, datetime] = {}
        self._last_score_per_asset: Dict[str, float] = {}
        self._alerts_this_hour: List[datetime] = []

    def _sentiment_points(self, sentiment: str) -> float:
        if sentiment == "POSITIVE":
            return 30.0
        if sentiment == "NEGATIVE":
            return -30.0
        return 0.0

    def _trim_hour_alerts(self):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        self._alerts_this_hour = [t for t in self._alerts_this_hour if t > cutoff]

    def run(
        self,
        tech_results: List[TechResult],
        sentiment_results: List[SentimentResult],
        asset_data: List[AssetData],
    ) -> List[DecisionRecord]:
        self.log("Computing final scores and alert decisions")
        sentiment_by_asset = {s.asset: s for s in sentiment_results}
        asset_by_name = {a.asset: a for a in asset_data}
        market_open = _is_market_hours_et()
        self._trim_hour_alerts()
        records: List[DecisionRecord] = []
        for tr in tech_results:
            sent = sentiment_by_asset.get(tr.asset)
            if sent:
                sent_points = self._sentiment_points(sent.sentiment)
            else:
                sent_points = 0.0
            final_score = (tr.tech_score * 0.70) + sent_points
            decision = "SKIP"
            skip_reason = None
            priority = 0
            if final_score >= ALERT_SCORE_THRESHOLD:
                # Check 24/7: outside market hours only 24/7 assets
                if not market_open and tr.asset not in ASSETS_24_7:
                    skip_reason = "Market closed; asset not 24/7"
                else:
                    last = self._last_alert_per_asset.get(tr.asset)
                    now = datetime.now(timezone.utc)
                    if last and (now - last).total_seconds() < ASSET_COOLDOWN_HOURS * 3600:
                        prev_score = self._last_score_per_asset.get(tr.asset, 0)
                        if final_score < prev_score + SCORE_BUMP_TO_OVERRIDE_COOLDOWN:
                            skip_reason = "Cooldown"
                    if not skip_reason and len(self._alerts_this_hour) >= MAX_ALERTS_PER_HOUR:
                        skip_reason = "Max alerts per hour"
                    if not skip_reason:
                        decision = "ALERT"
                        if final_score >= 90:
                            priority = 2
                        elif final_score >= 75:
                            priority = 1
                        else:
                            priority = 0
            records.append(DecisionRecord(
                asset=tr.asset,
                tech_score=tr.tech_score,
                sentiment=sent.sentiment if sent else "MIXED",
                final_score=round(final_score, 1),
                decision=decision,
                priority=priority,
                skip_reason=skip_reason,
            ))
            if decision == "ALERT":
                self._last_alert_per_asset[tr.asset] = datetime.now(timezone.utc)
                self._last_score_per_asset[tr.asset] = final_score
                self._alerts_this_hour.append(datetime.now(timezone.utc))
            self.log(f"{tr.asset}: final={final_score:.1f} -> {decision}" + (f" ({skip_reason})" if skip_reason else ""))
        return records
