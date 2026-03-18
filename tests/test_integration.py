"""Integration tests for Zion."""
from src.core import Zion

class TestZion:
    def setup_method(self):
        self.c = Zion()
    def test_10_ops(self):
        for i in range(10): self.c.process(i=i)
        assert self.c.get_stats()["ops"] == 10
    def test_service_name(self):
        assert self.c.process()["service"] == "zion"
    def test_different_inputs(self):
        self.c.process(type="a"); self.c.process(type="b")
        assert self.c.get_stats()["ops"] == 2
    def test_config(self):
        c = Zion(config={"debug": True})
        assert c.config["debug"] is True
    def test_empty_call(self):
        assert self.c.process()["ok"] is True
    def test_large_batch(self):
        for _ in range(100): self.c.process()
        assert self.c.get_stats()["ops"] == 100
