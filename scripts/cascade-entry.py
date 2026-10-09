#!/usr/bin/env python3
"""Russian entry VPS for a 3X-UI KIT exit VPS. Run on a fresh Debian/Ubuntu VPS."""

import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import tempfile
from urllib.parse import parse_qs, quote, urlsplit, urlunsplit
from urllib.request import urlopen
import uuid
import zipfile


VERSION = "v26.6.27"
ZIP_SHA256 = {
    "x86_64": "b3e5902d06d6282fe53cfa2fc426058b9aeaa429b2c812e20887cd47f26d08bf",
    "aarch64": "13a251379bea366c2cf10363ad71e75734193d401f26f518bf0c25e5c8f8c931",
}
ZIP_ARCH = {"x86_64": "64", "aarch64": "arm64-v8a"}
ROOT = Path("/etc/xray-cascade")
BIN = Path("/usr/local/bin/xray-cascade")
SERVICE = Path("/etc/systemd/system/xray-cascade.service")


def upstream_from_link(link):
    u = urlsplit(link.strip())
    if u.scheme != "vless" or not u.hostname or not u.port or not u.username:
        raise ValueError("нужна полная VLESS-ссылка латвийского KIT")
    user = str(uuid.UUID(u.username))
    q = {k: v[0] for k, v in parse_qs(u.query).items()}
    transport = q.get("type", "tcp")
    if q.get("security") != "reality" or transport not in ("tcp", "xhttp"):
        raise ValueError("поддерживаются VLESS + REALITY по TCP или XHTTP")
    if not q.get("sni") or not q.get("pbk") or not re.fullmatch(r"[0-9a-fA-F]{0,16}", q.get("sid", "")) or len(q.get("sid", "")) % 2:
        raise ValueError("в ссылке нужны sni, pbk и корректный sid")
    flow = q.get("flow", "")
    if transport == "xhttp" and flow:
        raise ValueError("XHTTP-ссылка не должна содержать flow")
    if flow not in ("", "xtls-rprx-vision"):
        raise ValueError("неподдерживаемый flow")
    if transport == "xhttp" and not q.get("path", "").startswith("/"):
        raise ValueError("XHTTP-ссылка должна содержать path")
    return {
        "address": u.hostname, "port": u.port, "id": user, "transport": transport,
        "flow": flow, "sni": q["sni"], "pbk": q["pbk"], "sid": q.get("sid", ""),
        "fp": q.get("fp", "chrome"), "spx": q.get("spx", "/"),
        "path": q.get("path", "/"), "mode": q.get("mode", "auto"),
    }


def build_config(state, upstream):
    user = {"id": upstream["id"], "encryption": "none"}
    if upstream["flow"]:
        user["flow"] = upstream["flow"]
    stream = {
        "network": upstream["transport"], "security": "reality",
        "realitySettings": {
            "serverName": upstream["sni"], "fingerprint": upstream["fp"],
            "publicKey": upstream["pbk"], "shortId": upstream["sid"], "spiderX": upstream["spx"],
        },
    }
    if upstream["transport"] == "xhttp":
        stream["xhttpSettings"] = {"path": upstream["path"], "mode": upstream["mode"]}
    return {
        "log": {"loglevel": "warning"},
        "inbounds": [{
            "tag": "phone", "listen": "0.0.0.0", "port": 443, "protocol": "vless",
            "settings": {"clients": [{"id": state["client_id"], "flow": "xtls-rprx-vision"}], "decryption": "none"},
            "streamSettings": {
                "network": "tcp", "security": "reality",
                "realitySettings": {
                    "show": False, "target": state["sni"] + ":443", "xver": 0,
                    "serverNames": [state["sni"]], "privateKey": state["private_key"],
                    "shortIds": [state["short_id"]],
                },
            },
        }],
        "outbounds": [{
            "tag": "latvia", "protocol": "vless",
            "settings": {"vnext": [{"address": upstream["address"], "port": upstream["port"], "users": [user]}]},
            "streamSettings": stream,
        }],
        "routing": {"rules": [{"type": "field", "inboundTag": ["phone"], "outboundTag": "latvia"}]},
    }


def client_link(state):
    query = (
        "type=tcp&security=reality&pbk=" + quote(state["public_key"], safe="")
        + "&fp=chrome&sni=" + quote(state["sni"], safe="")
        + "&sid=" + state["short_id"] + "&spx=%2F&flow=xtls-rprx-vision"
    )
    return urlunsplit(("vless", state["client_id"] + "@" + state["public_ip"] + ":443", "", query, "RU-to-LV"))


def run(*args):
    subprocess.run(args, check=True)


def install_binary():
    if BIN.exists():
        return
    machine = os.uname().machine
    if machine not in ZIP_ARCH:
        raise ValueError("поддерживаются только x86_64 и aarch64")
    url = f"https://github.com/XTLS/Xray-core/releases/download/{VERSION}/Xray-linux-{ZIP_ARCH[machine]}.zip"
    with urlopen(url, timeout=60) as response:
        data = response.read(100 * 1024 * 1024 + 1)
    if len(data) > 100 * 1024 * 1024:
        raise ValueError("архив Xray слишком большой")
    if hashlib.sha256(data).hexdigest() != ZIP_SHA256[machine]:
        raise ValueError("архив Xray не прошёл проверку SHA256")
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / "xray.zip"
        archive.write_bytes(data)
        with zipfile.ZipFile(archive) as zf:
            binary = zf.read("xray")
        temporary = Path(directory) / "xray"
        temporary.write_bytes(binary)
        temporary.chmod(0o755)
        run("install", "-m", "755", str(temporary), str(BIN))


def write_private(path, data):
    fd, name = tempfile.mkstemp(dir=ROOT)
    try:
        with os.fdopen(fd, "w") as out:
            json.dump(data, out, indent=2)
            out.write("\n")
        os.chmod(name, 0o600)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def new_state(public_ip, sni):
    if not ipaddress.IPv4Address(public_ip).is_global:
        raise ValueError("--public-ip должен быть публичным IPv4")
    if not re.fullmatch(r"[A-Za-z0-9.-]{1,253}", sni) or "." not in sni:
        raise ValueError("--sni должен быть именем сайта")
    keys = {}
    for line in subprocess.check_output([str(BIN), "x25519"], text=True).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            keys[key.strip()] = value.strip()
    private = keys.get("PrivateKey")
    public = keys.get("Password (PublicKey)") or keys.get("Password") or keys.get("PublicKey")
    if not private or not public:
        raise ValueError("Xray не выдал ключи REALITY")
    return {
        "public_ip": public_ip, "sni": sni, "client_id": str(uuid.uuid4()),
        "private_key": private, "public_key": public, "short_id": secrets.token_hex(8),
    }


def configure(args):
    if os.geteuid() != 0:
        raise ValueError("запустите от root")
    if sys.platform != "linux" or not Path("/run/systemd/system").exists():
        raise ValueError("нужен Linux с systemd")
    source = Path(args.upstream_file)
    if source.stat().st_mode & 0o077:
        raise ValueError("файл ссылки должен быть доступен только владельцу: chmod 600 " + str(source))
    with source.open() as stream:
        link = stream.read(4097).strip()
    if len(link) > 4096 or "\n" in link:
        raise ValueError("в файле должна быть ровно одна VLESS-ссылка")
    upstream = upstream_from_link(link)
    state_file, config_file = ROOT / "state.json", ROOT / "config.json"
    if args.command == "install" and state_file.exists():
        raise ValueError("каскад уже установлен; для смены второго участка используйте switch")
    if args.command == "switch" and not state_file.exists():
        raise ValueError("сначала выполните install")
    if args.command == "install":
        with socket.socket() as probe:
            try:
                probe.bind(("0.0.0.0", 443))
            except OSError as exc:
                raise ValueError("443/TCP уже занят на российском VPS") from exc
    ROOT.mkdir(mode=0o700, exist_ok=True)
    install_binary()
    state = json.loads(state_file.read_text()) if state_file.exists() else new_state(args.public_ip, args.sni)
    if upstream["address"] == state["public_ip"]:
        raise ValueError("латвийская ссылка указывает обратно на российский VPS")
    config = build_config(state, upstream)
    fd, temporary = tempfile.mkstemp(dir=ROOT, suffix=".json")
    try:
        with os.fdopen(fd, "w") as out:
            json.dump(config, out, indent=2)
        os.chmod(temporary, 0o600)
        run(str(BIN), "run", "-test", "-c", temporary)
        previous = config_file.read_bytes() if config_file.exists() else None
        os.replace(temporary, config_file)
        if args.command == "install":
            write_private(state_file, state)
            SERVICE.write_text("""[Unit]
Description=Xray cascade entry (RU to LV)
After=network-online.target
Wants=network-online.target

[Service]
DynamicUser=yes
LoadCredential=config.json:/etc/xray-cascade/config.json
AmbientCapabilities=CAP_NET_BIND_SERVICE
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ExecStart=/usr/local/bin/xray-cascade run -c %d/config.json
Restart=on-failure

[Install]
WantedBy=multi-user.target
""")
            try:
                run("systemctl", "daemon-reload")
                run("systemctl", "enable", "--now", "xray-cascade.service")
            except subprocess.CalledProcessError:
                subprocess.run(["systemctl", "disable", "--now", "xray-cascade.service"], check=False)
                SERVICE.unlink(missing_ok=True)
                config_file.unlink(missing_ok=True)
                state_file.unlink(missing_ok=True)
                raise
        else:
            try:
                run("systemctl", "restart", "xray-cascade.service")
            except subprocess.CalledProcessError:
                if previous is not None:
                    config_file.write_bytes(previous)
                    config_file.chmod(0o600)
                    run("systemctl", "restart", "xray-cascade.service")
                raise
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print("Клиентский профиль (адрес РФ; выход через латвийский VPS):")
    print(client_link(state))
    print("Откройте 443/TCP в файрволе VPS. Состояние: systemctl status xray-cascade")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    install = commands.add_parser("install", help="настроить свежий российский VPS")
    install.add_argument("--public-ip", required=True, help="публичный IPv4 российского VPS")
    install.add_argument("--sni", required=True, help="сайт для входящего REALITY")
    install.add_argument("--upstream-file", required=True, help="файл с одной VLESS-ссылкой латвийского KIT")
    switch = commands.add_parser("switch", help="сменить протокол РФ → Латвия без изменения профиля iPhone")
    switch.add_argument("--upstream-file", required=True)
    args = parser.parse_args()
    try:
        configure(args)
    except (ValueError, OSError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"Ошибка: {exc}\n")


if __name__ == "__main__":
    main()
