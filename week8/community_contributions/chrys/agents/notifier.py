"""NOTIFIER agent: format and send Pushover push."""
import time
from typing import List

import requests
from agents.base import AgentBase
from models import AlertPayload, TechResult, SentimentResult, DecisionRecord, AssetData

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


def _build_key_signals(tr: TechResult, asset_data: AssetData | None) -> List[str]:
    signals = []
    if tr.rsi and tr.rsi < 30:
        signals.append(f"RSI at {tr.rsi} — deeply oversold")
    elif tr.rsi and tr.rsi > 70:
        signals.append(f"RSI at {tr.rsi} — overbought")
    if tr.macd_signal == "BULLISH_CROSS":
        signals.append("MACD bullish crossover confirmed")
    elif tr.macd_signal == "BEARISH_CROSS":
        signals.append("MACD bearish crossover")
    if tr.bb_signal == "LOWER_BAND_BOUNCE":
        signals.append("Price at lower Bollinger Band — bounce signal")
    if tr.ema_cross == "GOLDEN_CROSS":
        signals.append("9 EMA crossed above 21 EMA (golden cross)")
    if tr.volume_spike and asset_data:
        signals.append(f"Volume {asset_data.volume_ratio}x above 20-day average")
    if not signals:
        signals.append("Technical signals reviewed")
    return signals[:5]


class NotifierAgent(AgentBase):
    name = "NOTIFIER"
    logger_name = "aria.notifier"

    def __init__(self, user: str = "", token: str = ""):
        super().__init__()
        self.user = user
        self.token = token

    def build_payload(self, record: DecisionRecord, tech: TechResult, sent: SentimentResult | None, asset_data: AssetData | None) -> AlertPayload:
        key_signals = _build_key_signals(tech, asset_data)
        return AlertPayload(
            asset=record.asset,
            bias=tech.bias,
            price=asset_data.price if asset_data else 0,
            change_24h=asset_data.change_24h if asset_data else "",
            tech_score=record.tech_score,
            sentiment=record.sentiment,
            narrative=sent.narrative if sent else "",
            final_score=record.final_score,
            key_signals=key_signals,
        )

    def send(self, payload: AlertPayload, priority: int) -> bool:
        if not self.user or not self.token:
            self.log("Pushover not configured; skipping send")
            return False
        title = f"🚨 {payload.bias} Alert: {payload.asset}"
        body = (
            f"📈 {payload.asset} is flashing a {payload.bias} signal.\n\n"
            f"💰 Price: ${payload.price:,.2f} ({payload.change_24h} in 24h)\n"
            f"📊 Tech Score: {payload.tech_score}/100\n"
            f"🗞️ Sentiment: {payload.sentiment} — \"{payload.narrative}\"\n"
            f"🔢 Opportunity Score: {payload.final_score}/100\n\n"
            "📉 Key Signals:\n" + "\n".join(f"• {s}" for s in payload.key_signals) + "\n\n"
            "⚠️ This is a trend alert, not financial advice. Always apply your own judgment."
        )
        data = {
            "token": self.token,
            "user": self.user,
            "title": title,
            "message": body[:1024],
            "priority": priority,
            "sound": "cashregister",
        }
        if priority == 2:
            data["retry"] = 30
            data["expire"] = 300
        for attempt in range(2):
            try:
                r = requests.post(PUSHOVER_URL, json=data, timeout=10)
                if r.status_code == 200:
                    self.log("Push sent successfully")
                    return True
                self.log(f"Pushover error {r.status_code}: {r.text}")
            except Exception as e:
                self.log(f"Push failed: {e}")
            if attempt == 0:
                time.sleep(5)
        return False

    def run(self, to_send: List[tuple[DecisionRecord, TechResult, SentimentResult | None, AssetData | None]]) -> None:
        self.log(f"Sending {len(to_send)} alert(s)")
        for record, tech, sent, asset_data in to_send:
            payload = self.build_payload(record, tech, sent, asset_data)
            self.send(payload, record.priority)
