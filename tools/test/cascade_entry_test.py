"""python3 -m unittest tools.test.cascade_entry_test"""
import importlib.util
from pathlib import Path
import unittest


path = Path(__file__).parents[2] / "scripts" / "cascade-entry.py"
spec = importlib.util.spec_from_file_location("cascade_entry", path)
cascade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cascade)

TCP = "vless://5f2c1e7a-0b3d-4c6e-9a8f-1234567890ab@198.51.100.7:443?type=tcp&security=reality&pbk=abc&fp=chrome&sni=example.com&sid=12ab&flow=xtls-rprx-vision#LV"
XHTTP = "vless://5f2c1e7a-0b3d-4c6e-9a8f-1234567890ab@198.51.100.7:8443?type=xhttp&security=reality&pbk=abc&fp=chrome&sni=example.com&sid=12ab&path=%2Fx&mode=auto#LV"
STATE = {"client_id": "11111111-2222-4333-8444-555555555555", "public_ip": "203.0.113.10", "sni": "cover.example.com", "short_id": "0123456789abcdef", "private_key": "private", "public_key": "public"}


class CascadeTest(unittest.TestCase):
    def test_switch_changes_only_second_hop(self):
        tcp = cascade.build_config(STATE, cascade.upstream_from_link(TCP))
        xhttp = cascade.build_config(STATE, cascade.upstream_from_link(XHTTP))
        self.assertEqual(tcp["inbounds"], xhttp["inbounds"])
        self.assertEqual(tcp["outbounds"][0]["streamSettings"]["network"], "tcp")
        self.assertEqual(xhttp["outbounds"][0]["streamSettings"]["network"], "xhttp")
        self.assertEqual(xhttp["outbounds"][0]["streamSettings"]["xhttpSettings"], {"path": "/x", "mode": "auto"})
        self.assertNotIn("flow", xhttp["outbounds"][0]["settings"]["vnext"][0]["users"][0])
        self.assertIn("flow=xtls-rprx-vision", cascade.client_link(STATE))
        self.assertIn("@203.0.113.10:443", cascade.client_link(STATE))

    def test_reject_unsafe_or_wrong_upstream(self):
        for link in (TCP.replace("security=reality", "security=none"),
                     XHTTP.replace("#LV", "&flow=xtls-rprx-vision#LV"), TCP.replace("sid=12ab", "sid=123"),
                     TCP.replace("vless://", "trojan://")):
            with self.subTest(link=link), self.assertRaises(ValueError):
                cascade.upstream_from_link(link)


if __name__ == "__main__":
    unittest.main()
