# Проверка каскада на двух VPS

## Полный KIT на российском VPS: выбор протокола в приложении

В этом варианте российский VPS запускает обычный KIT со всеми выбранными входящими протоколами. Команда `kit cascade set` направляет их трафик в латвийский KIT по одной ссылке VLESS + REALITY (TCP или XHTTP). Подписка берётся **с российского VPS**: приложение показывает те протоколы, которые оно поддерживает. AmneziaWG открывается отдельной ссылкой в AmneziaVPN, MTProto — отдельной ссылкой в Telegram. Профили OneXray зависят от поддержки форматов самим OneXray.

На латвийском VPS нужен установленный KIT и пользователь. Получите его ссылку:

```sh
kit user link test --all
```

Скопируйте **одну** ссылку `vless://` с `security=reality`, `type=tcp` либо `type=xhttp`. На российском VPS сохраните её в приватный файл:

```sh
umask 077
cat > /root/latvia-link.txt
```

После `cat` вставьте ссылку, нажмите `Ctrl+D`, затем выполните `chmod 600 /root/latvia-link.txt`. Если на российском VPS ещё работает прежний одиночный каскад, остановите его перед установкой KIT: `systemctl disable --now xray-cascade`. Его конфигурация останется в `/etc/xray-cascade`. На **Mac** в локальном клоне выполните (замените адрес сервера):

```sh
ssh root@RU_PUBLIC_IP 'apt-get update && apt-get install -y git && { test -d /root/3X-UI_KIT/.git || git clone --branch vps-cascade --single-branch https://github.com/duebchy/3X-UI_KIT.git /root/3X-UI_KIT; }'
scp scripts/3x-ui.sh scripts/kit.sh scripts/cascade-entry.py root@RU_PUBLIC_IP:/root/3X-UI_KIT/scripts/
```

`scp` нужен, пока изменения лежат только в локальном коммите и ещё не отправлены в GitHub. На **российском VPS** установите полный набор KIT и настройте каскад одной командой:

```sh
cd /root/3X-UI_KIT
bash scripts/3x-ui.sh --host RU_PUBLIC_IP --sni COVER_HOSTNAME --user test \
  --protocols reality,reality2,hy2,xhttp,ws,trojan,vmess,ss,tuic,wg,awg,awg3,mtproto \
  --cascade-upstream-file /root/latvia-link.txt
```

`--protocols all` не включает обычный WireGuard и второй REALITY; поэтому выше указан полный список. Для протоколов на отдельных портах откройте у хостера TCP/UDP-порты, которые покажет установщик (KIT на сервере настраивает UFW). Для подписки с доверенным сертификатом нужен 80/TCP при выпуске сертификата и 443/TCP для nginx. Если на российском VPS уже установлен полный KIT, повторная установка не нужна: перенесите обновлённые `kit.sh` и `cascade-entry.py`, затем на российском VPS выполните:

```sh
cd /root/3X-UI_KIT
install -d -m 755 /usr/local/lib/kit
install -m 755 scripts/cascade-entry.py /usr/local/lib/kit/cascade-entry.py
install -m 755 scripts/kit.sh /usr/local/bin/kit
kit cascade set --upstream-file /root/latvia-link.txt --user test
```

После настройки получите ссылки:

```sh
kit user link test
kit user link test --all
kit user link test --amnezia
kit user link test --telegram
kit check --deep
```

Первые две команды выдают российскую подписку и отдельные профили. Две следующие нужны только если соответствующие протоколы установлены; они не входят в обычную VPN-подписку. На телефоне проверьте по одному поддерживаемому профилю каждого протокола и внешний IP: сайты должны видеть IP латвийского VPS. `kit cascade set` можно запускать повторно после смены латвийской ссылки или добавления входящего протокола. Если команда сообщит о сбое, проверьте `kit check --deep` и журнал панели `tail -n 50 /var/log/x-ui/3xui.log`.

### Старый вариант с отдельной службой xray-cascade

Схема: **iPhone → российский VPS → латвийский VPS → интернет**. На телефоне два отдельных профиля: VLESS + REALITY/TCP на обоих участках и Hysteria2 на обоих участках. VLESS на втором участке можно переключить на XHTTP. На российском VPS работает служба `xray-cascade`.

Ниже команды для **двух чистых** VPS с Ubuntu 22.04/24.04 или Debian 12/13. Выполняйте их от `root` (при необходимости сначала `sudo -i`). В примерах замените `LV_PUBLIC_IP`, `RU_PUBLIC_IP` и `COVER_HOSTNAME` настоящими значениями. Используйте один и тот же коммит ветки `vps-cascade` на обоих VPS.

## 1. Латвийский VPS: выходной сервер

В панели хостинга откройте входящие **443/TCP** и **80/TCP**, а также оставьте SSH. На сервере:

```sh
apt-get update
apt-get install -y git
git clone --branch vps-cascade --single-branch https://github.com/duebchy/3X-UI_KIT.git /root/3X-UI_KIT
cd /root/3X-UI_KIT
git rev-parse HEAD
bash scripts/3x-ui.sh --protocols reality,xhttp --sni COVER_HOSTNAME --host LV_PUBLIC_IP --user test
```

`COVER_HOSTNAME` — доступный с латвийского VPS сайт с TLS 1.3 и HTTP/2. Используйте только имя сайта, без `https://`. Установщик покажет адрес панели и создаст пользователя `test`. Он ставит `kit.sh` и `kit-sub.py` **из этого клона**; автообновление KIT выключается. Панель 3X-UI и Xray скачиваются отдельно в версиях, заданных в установщике.

Проверьте установку:

```sh
kit check --deep
systemctl is-enabled kit-update.timer
kit user link test --all
```

`kit check --deep` должен проверить REALITY и XHTTP. Команда `systemctl is-enabled kit-update.timer` должна показать `disabled` или `not-found` (её код выхода при этом может быть ненулевым). В последнем выводе найдите **две** ссылки `vless://` с `security=reality`: одна с `type=tcp`, вторая с `type=xhttp`. Сначала скопируйте TCP-ссылку. Не сохраняйте её в Git и не присылайте вместе с паролем панели в публичный чат.

## 2. Российский VPS: входной сервер

В панели хостинга откройте входящий **443/TCP** и SSH. Порт 443 на сервере должен быть свободен. Выполните:

```sh
apt-get update
apt-get install -y git python3
git clone --branch vps-cascade --single-branch https://github.com/duebchy/3X-UI_KIT.git /root/3X-UI_KIT
cd /root/3X-UI_KIT
git rev-parse HEAD
umask 077
cat > /root/latvia-link.txt
```

После последней команды вставьте **одну TCP-ссылку** с латвийского VPS и нажмите `Ctrl+D`. Ссылка останется только в файле, а не в истории команд. Проверьте права:

```sh
chmod 600 /root/latvia-link.txt
python3 scripts/cascade-entry.py install --public-ip RU_PUBLIC_IP --sni COVER_HOSTNAME --upstream-file /root/latvia-link.txt
systemctl is-active xray-cascade
```

Для российского `--sni` нужен сайт с TLS 1.3 и HTTP/2, доступный **с российского VPS**; он может отличаться от латвийского. Скрипт скачает Xray v26.6.27 и сверит SHA256, затем выдаст клиентскую ссылку `vless://`. Сохраните её приватно: в ней ключ доступа к российскому VPS. `systemctl is-active` должен вывести `active`.

## 3. Проверка с iPhone

Добавьте **выданную российским скриптом** ссылку в OneXray и включите подключение. В профиле должен быть адрес `RU_PUBLIC_IP`, а тип — VLESS + REALITY/TCP. Откройте несколько сайтов и проверьте внешний IP: он должен совпадать с `LV_PUBLIC_IP`. Проверьте отдельно через Wi‑Fi и мобильную сеть, затем оставьте телефон с заблокированным экраном на некоторое время. Если значок VPN исчезнет, зафиксируйте время обрыва и журналы ниже: это поможет отделить проблему iOS-клиента от второго участка каскада.

## 4. Переключение РФ → Латвия на XHTTP

На латвийском VPS снова выполните `kit user link test --all` и скопируйте ссылку с `type=xhttp`. На российском VPS замените содержимое файла:

```sh
umask 077
cat > /root/latvia-link.txt
```

Вставьте **одну XHTTP-ссылку**, нажмите `Ctrl+D`, затем:

```sh
chmod 600 /root/latvia-link.txt
cd /root/3X-UI_KIT
python3 scripts/cascade-entry.py switch --upstream-file /root/latvia-link.txt
systemctl is-active xray-cascade
```

Повторите проверку сайтов и внешнего IP. Профиль на iPhone менять не нужно: его ключи и российский адрес не меняются. Для возврата к TCP вставьте прежнюю TCP-ссылку в файл и повторите `switch`.

## 5. Добавить отдельный маршрут Hysteria2

Эти команды подходят и для уже установленного каскада. VLESS останется на 443/TCP. Hysteria2 будет слушать **443/UDP** в РФ и **24443/UDP** в Латвии; откройте эти порты у хостеров и в файрволе.

Пока коммит есть только на Mac, перенесите два изменённых скрипта на VPS без публикации в GitHub. Выполните **на Mac** (замените адреса на свои):

```sh
scp /Users/duebchy/Documents/ChatGPT/TSPU/3X-UI_KIT-cascade/scripts/kit.sh root@LV_PUBLIC_IP:/root/3X-UI_KIT/scripts/kit.sh
scp /Users/duebchy/Documents/ChatGPT/TSPU/3X-UI_KIT-cascade/scripts/cascade-entry.py root@RU_PUBLIC_IP:/root/3X-UI_KIT/scripts/cascade-entry.py
```

На латвийском VPS обновите локальную команду KIT из проверенного клона, затем создайте Hysteria2 и прикрепите существующих пользователей:

```sh
cd /root/3X-UI_KIT
bash -n scripts/kit.sh
install -m 755 scripts/kit.sh /usr/local/bin/kit
kit hy2 add 24443
kit check --deep
kit user link test --all
```

В выводе должна появиться ссылка `hysteria2://`. Сохраните её в отдельном приватном файле на российском VPS. Команду `kit hy2 add` можно повторить: она прикрепит пользователей, которым вход ещё не назначен.

Для OneXray на российском входе Hysteria2 нужен доверенный TLS-сертификат. Домен не обязателен: [Let's Encrypt выдаёт сертификаты на IP](https://letsencrypt.org/2026/03/11/shorter-certs-certbot/), но они действуют около шести дней и требуют автоматического продления. Откройте **80/TCP** на российском VPS, затем установите Certbot 5.4+ и получите сертификат:

```sh
apt-get update
apt-get install -y python3-venv
python3 -m venv /opt/certbot
/opt/certbot/bin/pip install 'certbot>=5.4,<6'
/opt/certbot/bin/certbot certonly --standalone --preferred-profile shortlived --ip-address RU_PUBLIC_IP --non-interactive --agree-tos --register-unsafely-without-email
```

Настройте продление и перезапуск Xray после него:

```sh
install -d -m 755 /etc/letsencrypt/renewal-hooks/deploy
printf '#!/bin/sh\nsystemctl restart xray-cascade.service\n' > /etc/letsencrypt/renewal-hooks/deploy/restart-xray-cascade
chmod 755 /etc/letsencrypt/renewal-hooks/deploy/restart-xray-cascade
cat > /etc/systemd/system/cascade-cert-renew.service <<'EOF'
[Unit]
Description=Renew cascade TLS certificate
[Service]
Type=oneshot
ExecStart=/opt/certbot/bin/certbot renew --quiet
EOF
cat > /etc/systemd/system/cascade-cert-renew.timer <<'EOF'
[Unit]
Description=Check cascade TLS certificate daily
[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now cascade-cert-renew.timer
```

На российском VPS сохраните латвийскую Hysteria2-ссылку. Вставьте её после `cat`, затем нажмите `Ctrl+D`:

```sh
umask 077
cat > /root/latvia-hy2-link.txt
```

После `Ctrl+D` выполните:

```sh
chmod 600 /root/latvia-hy2-link.txt
cd /root/3X-UI_KIT
python3 scripts/cascade-entry.py enable-hy2 --upstream-file /root/latvia-hy2-link.txt --cert /etc/letsencrypt/live/RU_PUBLIC_IP/fullchain.pem --key /etc/letsencrypt/live/RU_PUBLIC_IP/privkey.pem
systemctl is-active xray-cascade
python3 scripts/cascade-entry.py links
```

Добавьте обе выданные российские ссылки в OneXray по отдельности. VLESS пойдёт через VLESS на оба сервера; Hysteria2 — через Hysteria2 на оба сервера. Ссылки содержат ключи доступа. Для сертификата на домен передайте `--server-name ДОМЕН` и пути к этому сертификату. Проверка продления: `/opt/certbot/bin/certbot renew --dry-run`.

## Если соединение не работает

- **На РФ VPS:** `journalctl -u xray-cascade -n 50 --no-pager` и `systemctl status xray-cascade --no-pager`. Если служба не запускается, проверьте свободный 443/TCP и файл `/root/latvia-link.txt`.
- **На латвийском VPS:** `kit check --deep` и `journalctl -u x-ui -n 50 --no-pager`. Убедитесь, что выбранная ссылка работает напрямую и что 443/TCP открыт у хостинга.
- **Если служба работает, а iPhone не подключается:** проверьте российский IP и входной SNI. С Mac проверьте `nc -vz -w 5 RU_PUBLIC_IP 443`: открытый TCP-порт ещё не подтверждает правильность ключей и маршрута до Латвии. Для Hysteria2 проверьте UDP-порты и сертификат. Не публикуйте полные журналы, ссылки и содержимое `/etc/xray-cascade`: там могут быть ключи.

Эта ветка предназначена для теста на пустых VPS. Изменения форка не подписаны ключом автора исходного проекта. Вручную проверяйте изменения коммита перед обновлением; режим ручного обновления KIT остаётся включённым после установки.
