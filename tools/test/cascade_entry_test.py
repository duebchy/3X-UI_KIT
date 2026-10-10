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
HY2 = "hysteria2://secret123@198.51.100.7:24443?sni=198.51.100.7#LV"
STATE = {"client_id": "11111111-2222-4333-8444-555555555555", "public_ip": "203.0.113.10", "sni": "cover.example.com", "short_id": "0123456789abcdef", "private_key": "private", "public_key": "public"}
HY2_STATE = dict(STATE, hy2={"auth": "phone-secret", "server_name": "203.0.113.10", "cert": "/etc/letsencrypt/live/203.0.113.10/fullchain.pem", "key": "/etc/letsencrypt/live/203.0.113.10/privkey.pem"})


class CascadeTest(unittest.TestCase):
    def test_xray_checks_json_named_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "state.json").write_text(json.dumps(STATE))
            (root / "config.json").write_text(json.dumps(cascade.build_config(STATE, cascade.upstream_from_link(TCP))))
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

    def test_kit_outbound_uses_same_validated_vless_link(self):
        tcp = cascade.outbound_from_link(TCP)
        xhttp = cascade.outbound_from_link(XHTTP)
        self.assertEqual(tcp["tag"], "kit-cascade-lv")
        self.assertEqual(tcp["settings"]["vnext"][0]["address"], "198.51.100.7")
        self.assertEqual(tcp["settings"]["vnext"][0]["users"][0]["flow"], "xtls-rprx-vision")
        self.assertEqual(xhttp["streamSettings"]["network"], "xhttp")
        self.assertNotIn("flow", xhttp["settings"]["vnext"][0]["users"][0])
        with self.assertRaises(ValueError):
            cascade.outbound_from_link(TCP.replace("security=reality", "security=none"))

    def test_reject_unsafe_or_wrong_upstream(self):
        for link in (TCP.replace("security=reality", "security=none"),
                     XHTTP.replace("#LV", "&flow=xtls-rprx-vision#LV"), TCP.replace("sid=12ab", "sid=123"),
                     TCP.replace("vless://", "trojan://")):
            with self.subTest(link=link), self.assertRaises(ValueError):
                cascade.upstream_from_link(link)

    def test_hysteria_has_separate_inbound_outbound_and_link(self):
        config = cascade.add_hy2(cascade.build_config(STATE, cascade.upstream_from_link(TCP)),
                                 HY2_STATE, cascade.hy2_upstream_from_link(HY2))
        self.assertEqual([i["protocol"] for i in config["inbounds"]], ["vless", "hysteria"])
        self.assertEqual([o["protocol"] for o in config["outbounds"]], ["vless", "hysteria"])
        self.assertEqual(config["routing"]["rules"][1]["outboundTag"], "latvia-hy2")
        self.assertEqual(config["outbounds"][1]["streamSettings"]["hysteriaSettings"]["auth"], "secret123")
        self.assertIn("@203.0.113.10:443?sni=203.0.113.10", cascade.hy2_client_link(HY2_STATE))

    def test_switch_preserves_hysteria(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "state.json").write_text(json.dumps(HY2_STATE))
            config = cascade.add_hy2(cascade.build_config(STATE, cascade.upstream_from_link(TCP)),
                                     HY2_STATE, cascade.hy2_upstream_from_link(HY2))
            (root / "config.json").write_text(json.dumps(config))
            upstream_file = root / "latvia-link"
            upstream_file.write_text(XHTTP)
            upstream_file.chmod(0o600)
            binary = root / "xray"
            binary.touch()
            original_exists = Path.exists

            def exists(path):
                return str(path) == "/run/systemd/system" or original_exists(path)

            class Checked(Exception):
                pass

            def check_config(*command):
                checked = json.loads(Path(command[4]).read_text())
                self.assertEqual(checked["outbounds"][0]["streamSettings"]["network"], "xhttp")
                self.assertEqual(checked["outbounds"][1]["protocol"], "hysteria")
                self.assertEqual(checked["inbounds"][1]["streamSettings"]["tlsSettings"]["certificates"][0]["certificateFile"], HY2_STATE["hy2"]["cert"])
                raise Checked()

            with mock.patch.object(cascade, "ROOT", root), mock.patch.object(cascade, "BIN", binary), \
                    mock.patch.object(Path, "exists", exists), mock.patch.object(cascade.os, "geteuid", return_value=0), \
                    mock.patch.object(cascade.sys, "platform", "linux"), mock.patch.object(cascade, "run", check_config):
                with self.assertRaises(Checked):
                    cascade.configure(SimpleNamespace(command="switch", upstream_file=str(upstream_file)))

    def test_reject_bad_hysteria_link(self):
        for link in (HY2.replace("sni=", "other="), HY2.replace("hysteria2://", "vless://"),
                     HY2.replace("#LV", "&insecure=true#LV")):
            with self.subTest(link=link), self.assertRaises(ValueError):
                cascade.hy2_upstream_from_link(link)

    def test_failed_hysteria_restart_restores_vless(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_file, config_file = root / "state.json", root / "config.json"
            state_file.write_text(json.dumps(STATE))
            config_file.write_text(json.dumps(cascade.build_config(STATE, cascade.upstream_from_link(TCP))))
            old_state, old_config = state_file.read_bytes(), config_file.read_bytes()
            upstream_file = root / "upstream"
            upstream_file.write_text(HY2)
            upstream_file.chmod(0o600)
            cert, key = root / "cert.pem", root / "key.pem"
            cert.touch(); key.touch()
            original_exists = Path.exists
            restarts = []

            def exists(path):
                return str(path) == "/run/systemd/system" or original_exists(path)

            def run(*command):
                if command[:2] == ("systemctl", "restart"):
                    restarts.append(command)
                    if len(restarts) == 1:
                        raise cascade.subprocess.CalledProcessError(1, command)

            with mock.patch.object(cascade, "ROOT", root), mock.patch.object(cascade, "HY2_DROPIN", root / "dropin" / "hy2.conf"), \
                    mock.patch.object(Path, "exists", exists), mock.patch.object(cascade.os, "geteuid", return_value=0), \
                    mock.patch.object(cascade.sys, "platform", "linux"), mock.patch.object(cascade, "run", run), \
                    mock.patch.object(cascade, "validate_config"), mock.patch.object(cascade, "validate_hy2_certificate"), \
                    mock.patch.object(cascade.socket, "socket"):
                with self.assertRaises(cascade.subprocess.CalledProcessError):
                    cascade.enable_hy2(SimpleNamespace(upstream_file=str(upstream_file), cert=str(cert), key=str(key), server_name=None))
            self.assertEqual(state_file.read_bytes(), old_state)
            self.assertEqual(config_file.read_bytes(), old_config)
            self.assertFalse((root / "dropin" / "hy2.conf").exists())
            self.assertEqual(len(restarts), 2)


if __name__ == "__main__":
    unittest.main()
