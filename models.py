from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

@dataclass
class DataResult:
    status: str
    data: Any
    source: str
    provider: str
    provider_version: str
    received_at: datetime
    market_timestamp: Optional[datetime]
    timeframe: str
    asset: str
    timezone: str
    quality_score: float
    freshness_score: float
    latency: float
    validation_errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    is_complete: bool = True
    is_proxy: bool = False
    proxy_instrument: Optional[str] = None
