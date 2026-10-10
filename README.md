<div align="center">

<img alt="3X-UI KIT" src="manuals/assets/banner.svg" width="820">

**Установка 3X-UI одной командой: 11 протоколов, один порт 443, одна подписка на всё**

[![Версия](https://img.shields.io/github/v/release/itsnotkubrick/3X-UI_KIT?label=3X-UI%20KIT&color=93E06F&labelColor=221B17)](https://github.com/itsnotkubrick/3X-UI_KIT/releases/latest)
[![Протоколов](https://img.shields.io/badge/протоколов-11-93E06F?labelColor=221B17)](manuals/3x-ui.md#протоколы)
[![3X-UI](https://img.shields.io/badge/3X--UI-v3.9.0-93E06F?labelColor=221B17)](https://github.com/MHSanaei/3x-ui)
[![Звёзды](https://img.shields.io/github/stars/itsnotkubrick/3X-UI_KIT?label=звёзды&style=flat&color=93E06F&labelColor=221B17)](https://github.com/itsnotkubrick/3X-UI_KIT/stargazers)
[![Обновлено](https://img.shields.io/github/last-commit/itsnotkubrick/3X-UI_KIT?label=обновлено&color=93E06F&labelColor=221B17)](https://github.com/itsnotkubrick/3X-UI_KIT/commits)

</div>

---

> [!WARNING]
> **Проект – набор скриптов с открытым кодом.** Он не оказывает услуг связи и не предоставляет доступ
> к серверам. Вы ставите его на собственный сервер и сами отвечаете за соблюдение законодательства
> своей страны. Проект создан в образовательных целях.

> [!NOTE]
> Это форк для проверки каскада на двух VPS. [Пошаговый гайд](manuals/cascade-two-vps.md).
> Установщик берёт `kit.sh` и `kit-sub.py` только из локального клона; автообновление KIT выключено.

**3X-UI KIT** превращает чистый VPS в готовый VPN-сервер за несколько минут. Скрипт ставит
официальную панель [3X-UI](https://github.com/MHSanaei/3x-ui), настраивает все популярные
протоколы, сертификат и файрвол и выдаёт одну ссылку-подписку. Её можно вставить в любое
приложение – оно само получит подходящие ему протоколы. Домен не нужен.

<div align="center">
<img alt="Конец установки 3X-UI KIT" src="manuals/assets/script-3x-ui.svg" width="760">
</div>

## Возможности

- 🧩 **11 протоколов на одном порту 443.** Панель, подписка и все TCP-протоколы спрятаны за одним портом,
  а на случайный заход сервер показывает обычный сайт. Протоколы: VLESS REALITY, VLESS XHTTP + REALITY,
  VLESS WebSocket + TLS, Trojan gRPC + TLS, VMess WebSocket + TLS, Shadowsocks 2022, Hysteria2, TUIC v5,
  AmneziaWG, AmneziaWG 3.1, MTProto (прокси для Telegram).
- 🔗 **Одна подписка на все приложения.** Hiddify, Happ, v2rayN, Karing, Clash Verge и FlClash
  получают свой формат и только те протоколы, которые распознают.
- 🧭 **Раздельная маршрутизация.** Через VPN идут только зарубежные сервисы, остальное – напрямую.
  Правила приезжают вместе с подпиской, DNS не течёт.
- 🥷 **Маскировка.** Со своим доменом на сервере стоит ваш сайт, без него сайт подбирается среди соседей
  по подсети. REALITY работает с `xtls-rprx-vision`.
- 👥 **Пользователи во все протоколы сразу.** Один пользователь – одна подписка, общий лимит трафика,
  срок и число устройств. Меню `kit` работает как у x-ui: выбрали цифру – готово.
- 💾 **Резервная копия и переезд на новый сервер одной командой.** Копия сохраняет подключения, ключи
  и пользователей, а на чистом VPS (даже с другим IP) сервер поднимается из неё за несколько минут.
- 🔄 **Обновления KIT в этом форке применяются вручную после проверки кода.**
- 🩺 **Проверка и починка сервера** одной командой.

## Что понадобится

- VPS с **Ubuntu 22.04/24.04** или **Debian 12/13** и доступом root по SSH
- Свободные порты **443** и **80** – на свежем сервере они свободны

Нужен VPS? Я сам использую **[IS Hosting](https://ishosting.io/affiliate/NTg4MiM4)** и рекомендую его
(реферальная ссылка).

## Установка

Подключитесь к серверу по SSH и клонируйте тестовую ветку на чистый VPS.

Панель 3X-UI, все протоколы на порту 443 и одна подписка на всё:

```bash
apt-get update
apt-get install -y git
git clone --branch vps-cascade --single-branch https://github.com/duebchy/3X-UI_KIT.git /root/3X-UI_KIT
cd /root/3X-UI_KIT
bash scripts/3x-ui.sh
```

Через пару минут скрипт покажет адрес панели, логин, пароль и подписку с QR-кодом.
Подробно – подключение приложений, дополнительные пользователи и параметры – в **[инструкции](manuals/3x-ui.md)**.

## Каскад через российский VPS (экспериментальный)

Полные команды для обоих серверов и проверок: **[гайд по каскаду](manuals/cascade-two-vps.md)**.

Для выбора протокола в приложении поставьте полный KIT и на российский VPS. Команда `kit cascade set --upstream-file /root/latvia-link.txt --user имя` добавит выход в латвийский KIT по VLESS + REALITY и направит туда все установленные входящие протоколы, включая MTProto через мост панели. `kit user link имя` выдаст подписку с российским адресом; для AmneziaVPN и Telegram есть отдельные ссылки. На чистом российском сервере установщик может сделать это сразу с `--cascade-upstream-file /root/latvia-link.txt`. [Команды и проверка](manuals/cascade-two-vps.md#полный-kit-на-российском-vps-выбор-протокола-в-приложении).

### Прежний вариант с отдельной службой

Этот режим оставляет 3X-UI KIT на выходном VPS, а на **отдельном чистом российском VPS** запускает Xray без панели. Телефон подключается к российскому VPS по VLESS + REALITY на 443/TCP. Второй участок VLESS можно переключать между REALITY/TCP и REALITY/XHTTP, не меняя профиль телефона. Дополнительно можно включить отдельный Hysteria2-маршрут на обоих участках; тогда телефон получит второй профиль. На обоих участках используются отдельные ключи.

1. На выходном VPS создайте пользователя и получите его ссылки: `kit user add имя`, затем `kit user link имя --all`. Выберите **одну** ссылку `vless://` с `security=reality` и `type=tcp` либо `type=xhttp`. Сохраните её на российском VPS в `/root/latvia-link.txt` с правами `600`. Не передавайте этот файл посторонним.
2. Скопируйте файл [`scripts/cascade-entry.py`](scripts/cascade-entry.py) из своей проверенной копии на российский VPS и выполните:

   ```sh
   python3 cascade-entry.py install --public-ip IP_РФ_VPS --sni САЙТ_МАСКИРОВКИ --upstream-file /root/latvia-link.txt
   ```

   Сайт маскировки должен отвечать по TLS 1.3 и HTTP/2 с российского VPS. Скрипт скачивает закреплённый Xray v26.6.27, проверяет SHA256, создаёт службу `xray-cascade` и выводит ссылку для телефона. Откройте 443/TCP в файрволе российского VPS и у хостера.
3. Чтобы переключить второй участок, замените файл ссылкой другого протокола того же выходного VPS и выполните `python3 cascade-entry.py switch --upstream-file /root/latvia-link.txt`. Клиентская ссылка и ключи входа останутся прежними. Проверка состояния: `systemctl status xray-cascade`.

На телефоне будет один или два профиля с российским адресом; внешний IP сайтов будет адресом выходного VPS. Скрипт предназначен для свежего Ubuntu/Debian с systemd, Python 3 и свободным 443/TCP (для Hysteria2 также 443/UDP). Изменение VLESS-ссылки на выходном VPS требует обновить файл и выполнить `switch`. Добавление Hysteria2 к уже установленному каскаду и настройка сертификата описаны в [гайде](manuals/cascade-two-vps.md).
Подпись `SHA256SUMS.sig` исходного проекта не покрывает изменения в форке; проверяйте свой коммит и копируйте файл из него.

## Команды KIT

После установки на сервере появляется команда `kit`. Запустите её **без аргументов** – откроется меню, как у `x-ui`: выберите цифру, остальное спросит само. Те же действия одной строкой – в группах ниже (нажмите, чтобы раскрыть). Подробности – в [инструкции](manuals/3x-ui.md).

<details>
<summary><b>Пользователи</b> – <code>kit user</code></summary>

```bash
kit user add имя [--gb 50] [--days 30] [--devices 3]   # добавить во все протоколы, показать подписку
kit user list                                          # кто сколько израсходовал, до какого числа
kit user link имя [--all | --amnezia | --telegram]     # подписка и ссылки «открыть в приложении»
kit user limit имя [--gb N] [--days N] [--devices N]   # изменить лимиты (0 – без ограничений)
kit user off имя  /  kit user on имя                   # выключить и включить
kit user del имя                                       # удалить
```
</details>

<details>
<summary><b>Сеть и маскировка</b> – <code>kit net</code></summary>

```bash
kit net                              # протоколы, порты, сайт маскировки, отпечаток – одним экраном
kit net site [сайт.com]              # сменить сайт маскировки (без аргумента – среди соседей по подсети)
kit net port имя порт                # сменить порт протокола
kit net off имя  /  kit net on имя   # выключить и включить протокол (kit net on reality2 – второй REALITY)
kit net fp firefox                   # сменить отпечаток клиента у всех подключений
kit net masq on|off                  # Hysteria2 отвечает на чужой запрос страницей сайта
kit net dns on|off                   # DNS в подписке по DoH через прокси
kit net panel domain | ip            # панель и подписка по своему домену или по IP
```
</details>

<details>
<summary><b>Раздельная маршрутизация</b> – <code>kit net split</code></summary>

Через VPN идёт только список зарубежных сервисов, остальное – напрямую. Подробнее – [в инструкции](manuals/3x-ui.md#раздельная-маршрутизация-kit-net-split).

```bash
kit net split on       # создать список и включить
kit net split check    # проверить список
kit net split apply    # после правки списка обновить профили Happ и Xray
kit net split off      # выключить
```
</details>

<details>
<summary><b>Обслуживание сервера</b> – проверка, обновление, копия</summary>

```bash
kit check [--deep] [--fix]   # проверить сервер; --deep – подключиться клиентом, --fix – исправить безопасное
kit update --manual          # проверить, что автообновление KIT выключено
kit panel update             # обновить панель 3X-UI до проверенной версии вручную
kit backup                   # копия сервера: подключения, ключи, пользователи
kit version                  # версии KIT, панели и ядра
```

Копию из `kit backup` на новом чистом сервере поднимает `bash 3x-ui.sh --restore файл`. Если подписка выдавалась
на домене, а не на IP, клиентам достаточно сменить адрес в DNS.
</details>

<details>
<summary><b>Если не подключается</b> – диагностика</summary>

```bash
kit check --deep             # проверить сервер и подключиться к нему клиентом: видно, виноват сервер или сеть
kit net fp firefox           # другой отпечаток клиента (вернуть: kit net fp chrome)
kit net site                 # другой сайт для маскировки
kit net on reality2          # дополнительный REALITY на другом порту
kit backup                   # не помогло – копия, затем перенос на другой адрес: на новом сервере bash 3x-ui.sh --restore файл
```

Один протокол не подключается – попробуйте соседний: у каждого свои сильные стороны (Hysteria2 работает по UDP,
остальные по TCP). В подписке Clash «Авто» выбирает сама, в остальных приложениях – вручную.
</details>

## VPN на роутере

Через прокси идут только нужные сервисы и выбранные устройства, остальное работает напрямую.
Порядок: **1.** установить программу на роутер → **2.** собрать конфиг в [генераторе](#генератор-конфигов-для-роутера) →
**3.** вставить команду из генератора.

> [!NOTE]
> На роутере работает [XKeen](https://github.com/jameszeroX/XKeen) автора jameszeroX, спасибо ему.

<details>
<summary><b>📶 Keenetic: XKeen (jameszeroX) · 8 шагов, 20–30 минут</b></summary>

Нужны роутер **Keenetic** или **Netcraze** с USB-портом, USB-флешка в формате **ext4** и свой сервер с VLESS
(например, из [этой инструкции](manuals/3x-ui.md)).

<details>
<summary><b>1. Компоненты KeeneticOS</b></summary>

В веб-интерфейсе: **Управление → Общие настройки → Изменить набор компонентов**. Отметьте компоненты
с галочками на картинке и установите. Роутер обновится и перезагрузится.

![Нужные компоненты KeeneticOS](manuals/assets/keenetic-components.svg)

</details>

<details>
<summary><b>2. Entware на флешку</b></summary>

1. Отформатируйте флешку в **ext4** и вставьте её в роутер.
2. Откройте её по сети (`\\192.168.x.x\`), создайте папку `install` и положите туда установщик под процессор роутера:
   [mipsel](https://bin.entware.net/mipselsf-k3.4/installer/mipsel-installer.tar.gz),
   [mips](https://bin.entware.net/mipssf-k3.4/installer/mips-installer.tar.gz) или
   [aarch64](https://bin.entware.net/aarch64-k3.10/installer/aarch64-installer.tar.gz).
   Не знаете, какой нужен? Модель роутера – в характеристиках на сайте Keenetic.

![Установщик Entware на флешке](manuals/assets/entware-installer.svg)

3. **Управление → OPKG**: выберите флешку и сохраните. Установка займёт несколько минут.

![Выбор накопителя для OPKG](manuals/assets/keenetic-opkg.svg)

</details>

<details>
<summary><b>3. Подключение по SSH</b></summary>

```bash
ssh root@192.168.x.x -p 222
```

Пароль по умолчанию `keenetic`. **Сразу смените его** командой `passwd`.

</details>

<details>
<summary><b>4. Шифрованный DNS</b></summary>

Пропишите шифрованные DNS-серверы (DoT или DoH) по
[инструкции Keenetic](https://support.keenetic.ru/ultra/kn-1811/ru/31543-dot-and-doh-proxy-servers-for-dns-requests-encryption.html):
без этого XKeen работает неправильно.

</details>

<details>
<summary><b>5. Токен для KeeneticOS 5.2 и новее</b></summary>

XKeen нужен токен доступа к роутеру. Создайте его в разделе **Пользователи и доступ**, вставьте в
[шаблон xkeen.json](https://github.com/jameszeroX/XKeen/releases/download/2.0.1_Beta/xkeen.json) и положите файл на роутер
по пути `/opt/etc/xkeen/xkeen.json`. Подробнее – в [вики XKeen](https://github.com/jameszeroX/XKeen/wiki/Порядок-установки).

</details>

<details>
<summary><b>6. Установка XKeen</b></summary>

Подключитесь по SSH и выполните:

```bash
opkg update && opkg upgrade && opkg install curl tar && cd /tmp
sh -c "$(curl -sSL https://raw.githubusercontent.com/jameszeroX/XKeen/main/install.sh)"
```

Если GitHub недоступен, замените адрес на `https://cdn.jsdelivr.net/gh/jameszeroX/XKeen@main/install.sh`.
Установщик спросит ядро (Xray или Mihomo), геобазы и автозагрузку.

Затем соберите конфиг в [генераторе](#генератор-конфигов-для-роутера) (роутер Keenetic, нужное ядро), вставьте команду в SSH-консоль
и нажмите Enter: файлы запишутся, XKeen перезапустится.

![Конфигурационные файлы Xray](manuals/assets/xkeen-configs.svg)

</details>

<details>
<summary><b>7. Какие устройства через прокси</b></summary>

В веб-интерфейсе откройте **Приоритеты подключений → Политики доступа в Интернет**, создайте политику
с именем **`xkeen`** и перенесите в неё нужные устройства.

> [!WARNING]
> Без политики `xkeen` через прокси пойдёт трафик **всех** устройств в сети.

</details>

<details>
<summary><b>8. Проверка</b></summary>

- На роутере: `xkeen -status` – XKeen должен быть запущен.
- На устройстве из политики `xkeen` откройте сайт, показывающий IP-адрес: он должен совпасть с адресом вашего сервера,
  а на остальных устройствах остаться прежним.
- Удобнее управлять настройками из браузера через [XKeen UI](https://github.com/zxc-rv/XKeen-UI).

</details>

Подробная версия с теми же шагами: [инструкция для Keenetic](manuals/xkeen-keenetic.md).

</details>

## Генератор конфигов для роутера

Вставьте ссылку на сервер или подписку, выберите роутер и ядро, отметьте нужные сервисы –
и получите готовый конфиг и одну команду, которая сама положит его на роутер.
Всё считается в браузере, ссылки никуда не отправляются.
Как поставить XKeen на роутер – в разделе [VPN на роутере](#vpn-на-роутере).

| Роутер | Ядро | Что получится | Генератор |
|---|---|---|---|
| Keenetic (XKeen) | Xray | `04_outbounds.json` и `05_routing.json`: серверы, выбор сервисов, реклама, свои сайты | [Открыть →](https://itsnotkubrick.github.io/3X-UI_KIT/tools/?core=xray) |
| Keenetic (XKeen) | Mihomo | `config.yaml` с автовыбором сервера, подпиской, Hysteria2, AmneziaWG и веб-панелью | [Открыть →](https://itsnotkubrick.github.io/3X-UI_KIT/tools/?core=mihomo) |
| OpenWrt (Nikki), бета | Mihomo | профиль для Nikki и команда, которая его включит | [Открыть →](https://itsnotkubrick.github.io/3X-UI_KIT/tools/?router=openwrt) |

## Полезное

- [XKeen](https://github.com/jameszeroX/XKeen) и его [вики](https://github.com/jameszeroX/XKeen/wiki) – документация по маршрутизации на Keenetic
- [XKeen UI](https://github.com/zxc-rv/XKeen-UI) – веб-интерфейс для XKeen
- [IP-адреса для AmneziaWG](https://github.com/RockBlack-VPN/ip-address) – актуальные списки от RockBlack

## Поддержать проект

Скрипты и инструкции бесплатные. Донат добровольный – он помогает оплачивать
тестовые серверы и держать скрипты в актуальном состоянии. Спасибо! 💜

| Способ | |
|---|---|
| Российской картой, СБП, Tinkoff Pay | [Tribute](https://t.me/tribute/app?startapp=dRsY) |
| Зарубежной картой, Apple Pay, Google Pay | [Buy Me a Coffee](https://buymeacoffee.com/relo.cate) |
| USDT (TRC-20) | `TS83ViXrdezUpp1eFadqj1rBhGLZaba1c1` |
| TON | `UQBchO4XFPwF9MMa_tjXpwqTo8IL2FhUDyllhYuFo8WM-Qbf` |
| Ethereum (ERC-20) | `0xC06F6B3A029d7Ea00705B7028490744e2BC16799` |

## Благодарности

3X-UI KIT построен на работе авторов этих проектов:
[3X-UI](https://github.com/MHSanaei/3x-ui) ·
[Xray-core](https://github.com/XTLS/Xray-core) ·
[Mihomo](https://github.com/MetaCubeX/mihomo) ·
[Hysteria](https://github.com/apernet/hysteria) ·
[AmneziaWG](https://github.com/amnezia-vpn) ·
[XKeen](https://github.com/jameszeroX/XKeen)
