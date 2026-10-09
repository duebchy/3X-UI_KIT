# Проверка каскада на двух VPS

Схема: **iPhone → российский VPS (VLESS + REALITY/TCP) → латвийский VPS (REALITY/TCP или REALITY/XHTTP) → интернет**. Телефон получает один профиль с российским адресом. На российском VPS нет панели 3X-UI: там работает отдельная служба `xray-cascade`.

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

## Если соединение не работает

- **На РФ VPS:** `journalctl -u xray-cascade -n 50 --no-pager` и `systemctl status xray-cascade --no-pager`. Если служба не запускается, проверьте свободный 443/TCP и файл `/root/latvia-link.txt`.
- **На латвийском VPS:** `kit check --deep` и `journalctl -u x-ui -n 50 --no-pager`. Убедитесь, что выбранная ссылка работает напрямую и что 443/TCP открыт у хостинга.
- **Если служба работает, а iPhone не подключается:** проверьте российский IP в профиле, доступность 443/TCP извне и правильность входного SNI. Не публикуйте полные журналы, ссылки и содержимое `/etc/xray-cascade`: там могут быть ключи.

Эта ветка предназначена для теста на пустых VPS. Изменения форка не подписаны ключом автора исходного проекта. Вручную проверяйте изменения коммита перед обновлением; режим ручного обновления KIT остаётся включённым после установки.
