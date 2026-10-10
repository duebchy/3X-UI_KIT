"""Exercise the KIT cascade command against a fake local 3X-UI API."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).parents[2]
SOURCE = (ROOT / "scripts" / "kit.sh").read_text()
LINK = "vless://5f2c1e7a-0b3d-4c6e-9a8f-1234567890ab@198.51.100.7:443?type=tcp&security=reality&pbk=abc&fp=chrome&sni=example.com&sid=12ab&flow=xtls-rprx-vision#LV"


def function(name, end="}"):
    return re.search(rf"^{name}\(\) [{{(].*?^{re.escape(end)}$", SOURCE, re.M | re.S).group(0)


class KitCascadeTest(unittest.TestCase):
    def run_command(self, failing_route=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            link = root / "link.txt"
            link.write_text(LINK)
            link.chmod(0o600)
            template = {"outbounds": [{"tag": "direct", "protocol": "freedom"}],
                        "routing": {"rules": [{"type": "field", "inboundTag": ["api"], "outboundTag": "api"}]}}
            (root / "panel.json").write_text(json.dumps(json.dumps({"xraySetting": template, "outboundTestUrl": "https://example.com/204"})))
            inbounds = [
                {"id": 1, "enable": True, "tag": "reality-in", "protocol": "vless", "settings": "{}"},
                {"id": 2, "enable": True, "tag": "telegram-in", "protocol": "mtproto", "settings": "{\"clients\":[],\"fakeTlsDomain\":\"example.com\"}"},
                {"id": 3, "enable": True, "tag": "tuic-in", "protocol": "tuic", "settings": "{}"},
                {"id": 4, "enable": True, "tag": "awg-in", "protocol": "amneziawg", "settings": "{}"},
                {"id": 5, "enable": False, "tag": "disabled-in", "protocol": "vmess", "settings": "{}"},
            ]
            for inbound in inbounds:
                inbound.update(remark=inbound["tag"], listen="", port=10000 + inbound["id"],
                               expiryTime=0, total=0, streamSettings="{}", sniffing="{}")
            (root / "inbounds.json").write_text(json.dumps(inbounds))
            script = "\n".join(function(n, ")" if n == "cmd_cascade_set" else "}") for n in
                               ("cmd_cascade_set", "cascade_apply_inbound", "cascade_rollback", "cascade_apply", "inbound_body_of"))
            script = script.replace("/etc/kit/cascade.", str(root / "cascade."))
            script = script.replace("/usr/local/lib/kit/cascade-entry.py", str(ROOT / "scripts" / "cascade-entry.py"))
            stubs = r'''
set -Eeuo pipefail
API=http://panel; XUI_API_TOKEN=test-token; HOST=203.0.113.10
valid_name() { :; }; need_val() { [[ -n ${2-} ]]; }; die() { echo "ERROR: $*" >&2; exit 1; }
say() { echo "$*"; }; warn() { echo "WARN: $*" >&2; }
client() { echo '{"subId":"test-sub"}'; }; cmd_link() { echo SUBSCRIPTION_OK; }
ss() { echo 'LISTEN 0 4096 127.0.0.1:34567'; }
api() {
  case "$1 $2" in
    'POST xray/') cat "$ROOT_DIR/panel.json" ;;
    'GET inbounds/list') cat "$ROOT_DIR/inbounds.json" ;;
    'GET inbounds/get/2') echo '{"settings":"{\"routeXrayPort\":34567}"}' ;;
    'POST server/restartXrayService') echo null ;;
    *) return 1 ;;
  esac
}
curl() {
  local url=${@: -1} a file=
  for a in "$@"; do
    [[ $a == xraySetting@* || $a == @* ]] && file=${a#*@}
  done
  case "$url" in
    */xray/update) cp "$file" "$ROOT_DIR/applied.json"; echo '{"success":true}' ;;
    */inbounds/update/2) cp "$file" "$ROOT_DIR/mt-applied.json"; echo '{"success":true}' ;;
    */xray/routeTest)
      if [[ $FAIL_ROUTE == yes ]]; then echo '{"success":true,"obj":{"matched":true,"outboundTag":"direct"}}';
      else echo '{"success":true,"obj":{"matched":true,"outboundTag":"kit-cascade-lv"}}'; fi ;;
    *) return 1 ;;
  esac
}
'''
            command = stubs + script + '\ncmd_cascade_set --upstream-file "$ROOT_DIR/link.txt" --user test\n'
            result = subprocess.run(["bash", "-c", command], capture_output=True, text=True,
                                    env={"PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin", "ROOT_DIR": directory,
                                         "FAIL_ROUTE": "yes" if failing_route else "no"})
            applied = json.loads((root / "applied.json").read_text())
            mt = json.loads((root / "mt-applied.json").read_text())
            return result, applied, mt, template

    def test_routes_all_enabled_protocols_and_preserves_panel_api(self):
        result, applied, mt, _ = self.run_command()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SUBSCRIPTION_OK", result.stdout)
        self.assertEqual(applied["routing"]["rules"][0]["inboundTag"],
                         ["reality-in", "telegram-in", "tuic-in", "awg-in"])
        self.assertEqual(applied["routing"]["rules"][1]["outboundTag"], "api")
        self.assertEqual(applied["outbounds"][1]["protocol"], "vless")
        self.assertTrue(json.loads(mt["settings"])["routeThroughXray"])

    def test_route_check_failure_rolls_back_both_settings(self):
        result, applied, mt, template = self.run_command(failing_route=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(applied, template)
        self.assertNotIn("routeThroughXray", json.loads(mt["settings"]))


if __name__ == "__main__":
    unittest.main()
