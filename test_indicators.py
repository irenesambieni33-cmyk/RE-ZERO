import pandas as pd
import numpy as np
from indicators.indicator_engine import IndicatorEngine

def test_indicators():
    n = 250
    x = pd.DataFrame({
        "Open": np.arange(n)+1,
        "High": np.arange(n)+2,
        "Low": np.arange(n),
        "Close": np.arange(n)+1.5,
        "Volume": np.ones(n)*100
    })
    y = IndicatorEngine().calculate(x)
    assert "RSI_14" in y.columns
    assert "ATR_14" in y.columns
