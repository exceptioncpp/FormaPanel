# RH-01: просмотр настоящего LVGL в Home Assistant

`index.html` показывает два PNG 480×480 из host-сборки ESPHome с настоящим
LVGL. Браузер не перерисовывает текст, фон или виджеты. Кнопки, невидимая
область светильника и автопоказ переключают сохранённые кадры. Показания
демонстрационные; страница не вызывает сервисы Home Assistant.

Опубликованный просмотр: [FormaPanel Preview](http://ha.home.arpa/formapanel-preview/native).
Отдельная страница: [снимки LVGL](http://ha.home.arpa/local/formapanel-preview/native/index.html).

Файлы размещаются в `/config/www/formapanel-preview/native/`:

- `index.html` из этой папки;
- `rh01-on.png` и `rh01-off.png` из `reports/local/native-preview/`;
- `preview.json` с версией ESPHome и SHA-256 обоих кадров.

Текущие снимки получены ESPHome **2026.10.1** 31.10.2026 на существующем
компиляторе HA. Повторная сборка/захват: локальный помощник
`reports/local/native_preview_ha.py`, команды `deploy`, `build`, `fetch`.
Публикация для этого окружения: `python reports/local/publish_native_preview.py`.
Оба помощника остаются вне Git, поскольку используют местную SSH/QEMU-схему.

В HA создана отдельная storage-панель `formapanel-preview` с одной panel-view
`native` и обычной iframe-карточкой. Используются штатные WebSocket-команды
`lovelace/dashboards/create`, `lovelace/config/save` и чтение для проверки;
перезапуск HA, дополнительные приложения и изменение существующих панелей
не требуются. Перед повторной публикацией сохраняются заменяемые файлы и
настройки в `/config/formapanel-preview-backups/<UTC timestamp>/`.

Токены и пароли не попадают в HTML, PNG или `preview.json`. В публичную `/local/`
папку копируются только эти четыре файла. Снимок host-LVGL проверяет компоновку
и растеризацию, а цвет и поведение физического дисплея проверяются отдельно.

Основание реализации: [HA WebSocket API](https://developers.home-assistant.io/docs/api/websocket/),
[официальные команды dashboard](https://github.com/home-assistant/frontend/blob/dev/src/data/lovelace/dashboard.ts),
[сохранение Lovelace-конфигурации](https://github.com/home-assistant/core/blob/2026.10.1/homeassistant/components/lovelace/websocket.py),
[iframe-карточка](https://www.home-assistant.io/dashboards/iframe/).
