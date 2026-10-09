"""python3 -m unittest tools.test.cascade_entry_test"""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


path = Path(__file__).parents[2] / "scripts" / "cascade-entry.py"
spec = importlib.util.spec_from_file_location("cascade_entry", path)
cascade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cascade)

TCP = "vless://5f2c1e7a-0b3d-4c6e-9a8f-1234567890ab@198.51.100.7:443?type=tcp&security=reality&pbk=abc&fp=chrome&sni=example.com&sid=12ab&flow=xtls-rprx-vision#LV"
XHTTP = "vless://5f2c1e7a-0b3d-4c6e-9a8f-1234567890ab@198.51.100.7:8443?type=xhttp&security=reality&pbk=abc&fp=chrome&sni=example.com&sid=12ab&path=%2Fx&mode=auto#LV"
STATE = {"client_id": "11111111-2222-4333-8444-555555555555", "public_ip": "203.0.113.10", "sni": "cover.example.com", "short_id": "0123456789abcdef", "private_key": "private", "public_key": "public"}


class CascadeTest(unittest.TestCase):
    def test_xray_checks_json_named_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "state.json").write_text(json.dumps(STATE))
            upstream_file = root / "latvia-link"
            upstream_file.write_text(TCP)
            upstream_file.chmod(0o600)
            binary = root / "xray"
            binary.touch()
            original_exists = Path.exists

            def exists(path):
                return str(path) == "/run/systemd/system" or original_exists(path)

            class Checked(Exception):
                pass

            def check_config(*command):
                self.assertEqual(command[:4], (str(binary), "run", "-test", "-c"))
                self.assertEqual(Path(command[4]).suffix, ".json")
                json.loads(Path(command[4]).read_text())
                raise Checked()

            with mock.patch.object(cascade, "ROOT", root), mock.patch.object(cascade, "BIN", binary), \
                    mock.patch.object(Path, "exists", exists), mock.patch.object(cascade.os, "geteuid", return_value=0), \
                    mock.patch.object(cascade.sys, "platform", "linux"), mock.patch.object(cascade, "run", check_config):
                with self.assertRaises(Checked):
                    cascade.configure(SimpleNamespace(command="switch", upstream_file=str(upstream_file)))

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
