class CapabilityRegistry:
    def __init__(self):
        self.capabilities = {
            "OHLC DATA AVAILABLE": True,
            "VOLUME AVAILABLE": True,
            "REAL ORDER FLOW UNAVAILABLE": False,
            "DIRECT XAU/USD UNAVAILABLE": False,
            "GC=F PROXY AVAILABLE": True,
            "MACRO LIVE DEGRADED": False,
            "BROKER EXECUTION UNAVAILABLE": False,
            "PAPER TRADING AVAILABLE": True,
        }
    def snapshot(self):
        return dict(self.capabilities)
