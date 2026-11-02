# Интеграция FormaPanel Living с Home Assistant — 02.11.2026

## Активировано в HA

HA Core 2026.10.4. Отдельный пакет установлен в /config/packages/formapanel_living.yaml после backup и успешного /api/config/core/check_config (valid, без errors/warnings).

- [Рабочий пакет](../../config/ha/packages/formapanel-living-runtime.yaml): сохраняемые mode/target/manual heat/manual cool/light request/brightness, пять прогнозных кэшей, два скрипта и автоматизация погоды.
- [46 определений шаблонных helpers](../../config/ha/formapanel-living-template-helpers.json) созданы как **отдельные конфигурационные записи** стандартной интеграции Template. Каждая зарегистрирована под ожидаемым entity_id и назначена area gostinaia. Определения не дублируются в активном YAML.
- T/RH гостиной читаются из существующих sensor.home_living_temperature/humidity через комнатные абстракции. CO₂, фактическое состояние основного света/HVAC пока неизвестны — опубликованы как unavailable, без фиктивных нулей.
- target инициализирован существующей уставкой гостиной 24°C, desired brightness — 100%, TTL — 10800 секунд. Начальные значения сохраняемых helpers не закреплены initial: при обычном рестарте HA восстанавливает последнее значение.
- contract_ready=on означает готовность виртуального интерфейса. Physical ready=off и backend_status=unbound: отсутствующие исполнители не имитируются. Ручные одновременные heat+cool отображаются как conflict. Существующие TPI и его расписания остаются владельцами реального отопления.

## Погода

Текущая погода — Яндекс.Погода, Gismeteo — резерв. Проверены реальные сервисные ответы: Яндекс даёт горизонт до завтра; Gismeteo — семь суток. Для общего ряда выбирается один поставщик с большим числом валидных ближайших пяти дат; при равенстве приоритет Яндексу. Сейчас прогноз целиком Gismeteo, источник отображается отдельно от текущей погоды.

Обновление — каждые 30 минут, при старте HA и явным script.formapanel_living_weather_refresh. У каждой строки exact date, high, nullable low, condition, source и received_at. Пять input_text кэшей максимум 255 символов. Дни разных поколений/источников не публикуются вместе. При потере/просрочке данных публикуется unavailable, без zero/demo fallback. TTL проверяет liveness последнего отчёта поставщика; received_at не объявляется временем выпуска прогноза. 10800 секунд включает запас к фактически настроенному периоду Яндекса 7200 секунд. Частота внешней интеграции не менялась.

Формат подписки firmware: weather_day_0…4 — high; отдельные weather_day_N_low, _condition, _date. Это заменяет ранний проект с атрибутами. Новая схема нужна для изолированного включения helpers без общей перезагрузки Template.

## Почему не выполнялся template.reload

Во время работ спальня реально нагревалась: target 28°C, T 27.21°C, TPI/output 100%. Общая перезагрузка YAML Template могла кратко сбросить gate и интегратор. Поэтому использован поддерживаемый UI config-flow для новых Template entities; действующие шаблоны и климатические автоматизации не останавливались.

Выполнены только сохраняющие прежние значения reload helper domains и script, затем automation.reload с конкретным id=formapanel_living_weather_refresh. Старые config YAML сохранили hash; сравнение состояний действующих контролов до/после изменений не выявило расхождений. Никакие climate.*, физические light/switch или global source команды не вызывались.

## Панель и прошивка

Добавленная владельцем [FormaPanel Living](http://ha.local/config/devices/device/1785097fd4993e8aa91770637030d90f) подтверждена: IP192.168.0.190, MAC28:37:2f:8a:06:40, area gostinaia, ESPHome config entry01M6DHZSM9VMENBFASZV3PSHTW. Ключи в отчёт не входят.

Новая firmware использует виртуальные T/RH/CO₂, подтверждаемый запрос яркости, contract_ready и отдельные поля пятидневного прогноза. Состояние pending/timeout/error не подменяет физическое подтверждение. Авто показывает неподключённое оборудование. Все panel action targets остаются явными комнатными input helpers/script; scope не выбирается по произвольному entity_id.

Native job 1793604519541-living: 12/12 кадров, модель и реальные события PASS. Firmware job 1793604552430-living: factory+OTA успешно собраны с тем же source fingerprint ca9f1e71a74225953769a7238e3a4695b66473224788c97e4a8eac6859edcc4c.

На момент этой записи **allow_service_calls не включено**: auto-review потребовал явного согласия на широкое разрешение HA; вопрос задан владельцу. **Новая OTA ещё не выполнена**: ожидается согласие на перезагрузку одной панели. Не путать готовую сборку с работающей на устройстве версией.

## Проверки

- 13 изолированных сценариев с настоящим HA Script engine: live Yandex/Gismeteo responses, отказ сервиса, пустой/просроченный/частично записанный кэш, отсутствующий минимум, неверная дата/condition, выбор поставщика, восстановление, TTL0.
- Live HA: режим и target; manual heat/cool/conflict; desired brightness; два light toggle; отсутствие физического actual; TTL0 → unavailable → восстановление всех пяти дней. Все исходные helper значения восстановлены. Изменений действующих контролов: 0.
- Все 46 независимых Template entities зарегистрированы и назначены гостиной. Реальная температура/влажность/погода получены из HA, демо-значения в HA не устанавливались.

## Backup и откат

Пакет и исходная конфигурация: /config/formapanel-ha-backups/runtime-20261102T072648Z. Template registry/config entries backup и журнал созданных entry_id: /config/formapanel-backups/template-helpers-20261102T072714Z-fb82be0a (каталог0700, файлы0600; содержит секреты других интеграций и не публикуется).

Для отката новых сущностей использовать точные entry_id журнала и штатный config-entry API; **не восстанавливать целиком core.config_entries поверх последующих пользовательских изменений**. Сначала отключить только новую weather automation, затем удалить только принадлежащие этой установке записи/пакет после проверки hash. Reload только соответствующих helper domains/script и конкретного weather automation id; глобальный template.reload не нужен. Физические устройства и настройки TPI откатывать не требуется: они не менялись.

firmware.factory.bin: 2240752 bytes; SHA-256 272232a2063b2fe8d1a791794ee00978e4a0510d0654ca4ac7adfe9c990ddec8.

firmware.ota.bin: 2175216 bytes; SHA-256 c7d71845126f0a4308832d4e3e4b1f7ae07a8f5be4b97488bacc52bdd069b871.
