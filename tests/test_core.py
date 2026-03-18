"""Tests for Zion."""
from src.core import Zion
def test_init(): assert Zion().get_stats()["ops"] == 0
def test_op(): c = Zion(); c.process(x=1); assert c.get_stats()["ops"] == 1
def test_multi(): c = Zion(); [c.process() for _ in range(5)]; assert c.get_stats()["ops"] == 5
def test_reset(): c = Zion(); c.process(); c.reset(); assert c.get_stats()["ops"] == 0
def test_service_name(): c = Zion(); r = c.process(); assert r["service"] == "zion"
