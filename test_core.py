from core.capability_registry import CapabilityRegistry
def test_capabilities():
    c = CapabilityRegistry().snapshot()
    assert c["GC=F PROXY AVAILABLE"] is True
