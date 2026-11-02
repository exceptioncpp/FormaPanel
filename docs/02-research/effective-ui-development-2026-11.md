# Практический цикл разработки UI, ноябрь 2026

Срез **01.11.2026**, проект FormaPanel: **ESPHome 2026.10.1 / LVGL 9.5.0**.
Здесь разделены уже работающий процесс и возможные расширения. Настройка среды:
[браузерный workflow](ha-browser-workflow.md),
[проверки Workshop](../06-validation/ha-workshop-2026-10-31.md).

## Что использовать сейчас

Основной путь: **Studio Code Server → Save → кнопка preview в Workshop →
реальный LVGL PNG → проверка поведения → firmware build → финальная OTA**.
Редактор и сборщик используют один Git checkout на HA. Весь многофайловый проект
не нужно превращать в формат визуального редактора и переносить обратно.

| Задача | Инструмент и статус |
|---|---|
| Править настоящий проект с packages, assets и комнатными профилями | **Работает:** Studio Code Server, общий checkout `/config/esphome/formapanel-rh01` |
| Проверить реальные шрифты, RGB565/alpha, композицию и страницы | **Работает:** Workshop, ESPHome host + snapshot, PNG из настоящего LVGL |
| Получать сборку сразу после Save | **Пока не реализовано:** после сохранения нажать кнопку; stale показывает необходимость новой сборки |
| Быстро накидать виджеты визуально | **Кандидат:** ESPboards, экспорт только UI-фрагмента; интеграционный PoC ещё нужен |
| Выбирать HA entities и смотреть их значения в visual editor | **Установлен, ограничен:** koosoli ESPHomeDesigner RC48, LVGL экспериментален |
| Нажимать/перетаскивать настоящий ESPHome/LVGL UI в браузере | **Предложено, не установлено:** host + SDL + Linux X display + VNC/noVNC |
| Мгновенно посмотреть фиксированную композицию RH-01 | **Есть отдельный JS preview:** он не универсальный parser многофайлового ESPHome и не замена native рендеру |

В Workshop **0.1.1** от 01.11 исправлены стабильные пути wrapper и ESPHome
metadata для повторных сборок; [настройки](../../../../docs/infrastructure/ha-formapanel-workshop.md)
описаны отдельно. Проверенный срез **01.11.2026**, профиль RH-01:

| Повторный job | Validate + compile + render на сервере | Compile steps |
|---|---:|---:|
| UI не изменён | 6.19 с | 0 |
| Реальная правка layout: clock `x: 29 → 31` | 7.88 с | 3 |
| Возврат clock `x: 29` | 6.64 с | 3 |

В каждом job получены два native PNG, build tree не очищался. Изменённый кадр
отличался только областью часов `(32, 103)–(219, 156)`; проверенный PNG после
возврата source побитно совпал с исходным. Оригинальные source восстановлены.
Первый холодный прогон после миграции в эту таблицу не включён; браузерный
polling добавляет до 2 с к отображению готового результата. Это не обещание
универсального Save → кадр: автоматического старта по Save пока нет, а новые
шрифты, assets и более сложный layout могут потребовать больше времени.
Evidence: локальный `reports/local/workbench-smoke/incremental-benchmark-2026-11-01.json`.

## Разделить внешний вид, поведение и комнату

Для нового визуально редактируемого экрана полезен такой **предлагаемый** контракт:

```text
firmware/esphome/
  packages/ui/generated/layout.yaml    # только результат visual layout
  packages/ui/resources.yaml           # общие PNG, TTF, styles
  packages/ui/events.yaml              # !extend: виджет → стабильный script ID
  packages/behavior/mock.yaml          # значения/действия без HA
  packages/behavior/ha.yaml            # HA state input и action output
  packages/pages/info.yaml             # общий вторичный экран
  profiles/{living,bedroom}.yaml       # значения, entity IDs, набор страниц
  targets/<room>.yaml                  # аппаратный entry + HA behavior
  previews/<room>.yaml                 # тот же UI + mock behavior + host backend
```

Эти новые пути — схема следующего экрана, не описание уже созданных файлов.
Сегодня общий home находится в `packages/rh01-ui.yaml`, info — в
`packages/info-page.yaml`; существующие profiles/targets/previews уже работают.

Для новых функций удобнее брать `living` или `bedroom`: firmware и preview
подключают один комнатный profile. RH-01 остаётся фиксированным визуальным
эталоном: его `previews/host-rh01.yaml` отдельно задаёт demo substitutions.
Правка demo-значения только в аппаратном `formapanel-rh01.yaml` не меняет эти
preview-значения. Общий `rh01-ui.yaml` используется во всех трёх вариантах.

У generated-файла один владелец: visual exporter. Ручные HA actions, scripts,
availability и room substitutions живут рядом. Экспорт не должен менять GPIO,
Wi-Fi, API, OTA, secrets и аппаратные настройки. ID вроде `ui_demo_toggle`,
`ui_demo_level`, `ui_demo_status` сохранять между экспортами. До изменения ID
проверить ссылки в behavior, mocks и capture backend.

ESPHome [`!extend`](https://esphome.io/components/packages/#extend) позволяет
добавлять поведение к существующему ID в списке. Например, для **новой** страницы
с заранее созданной кнопкой, без повторного объявления её внешнего вида:

```yaml
# packages/ui/events.yaml — иллюстрация контракта, не установленный пакет
lvgl:
  pages:
    - id: !extend ui_controls
      widgets:
        - button:
            id: !extend ui_demo_toggle
            on_click:
              - script.execute: ui_demo_toggle_request
```

Mock и HA пакеты определяют один и тот же script ID, но подключается только
один из них. Для слайдера аналогично отделить событие от action: отправлять
завершённое значение на release либо с осознанным ограничением частоты.
Программное обновление виджета входным HA state не должно вызывать обратную
команду: проверить event semantics выбранного виджета и защиту от такого цикла.

Общие страницы подключаются один раз. Комната выбирает главную композицию,
подставляет свои entity IDs и значения, сохраняя общие resources/info/settings.
При другой главной странице не подключать старый home вторым экземпляром.
Нынешний capture backend знает `rh01_home`, `rh01_lamp_image`, `panel_info`:
для новых ID нужен новый capture сценарий, а не ожидание автоматического обхода
всех возможных состояний и страниц.

## Визуальный layout через ESPboards

ESPboards удобно использовать как редактор геометрии, стилей и дерева виджетов.
По его текущей [таблице поддержки](https://lvgl.espboards.dev/help/widget-support/)
Triggers, Actions и Entity bindings отсутствуют. Поэтому наличие красивой
кнопки в canvas не означает готовое управление HA.

Практический цикл для одного фрагмента:

1. Создать/импортировать только выбранный `lvgl:` UI со стабильными ID.
2. Расставить виджеты и размеры, проверить их в editor preview.
3. Через YAML export сохранить только допустимые layout/resources секции в
   `packages/ui/generated/layout.yaml`. Формат и кнопки описаны в
   [user guide](https://lvgl.espboards.dev/help/user-guide/).
4. Посмотреть Git diff: не исчезли ли ID, states, nesting, fonts, styles,
   image references; отсутствуют ли неожиданные hardware/network секции.
5. Поведение из `events.yaml` / `behavior/*.yaml` не экспортировать обратно
   в canvas. Следующий экспорт layout не должен его перезаписывать.
6. Validate и native preview выполнить в нашей pinned ESPHome среде.

Это добровольный **UI-only** путь с переносом одного фрагмента, а не новый
обязательный этап между IDE и сборщиком. Если даже такой экспорт не нужен,
остаться на редактировании YAML в общем checkout.

## ESPHomeDesigner: где полезен и что означает Save

[Koosoli ESPHomeDesigner](https://github.com/koosoli/ESPHomeDesigner) предлагает
entity picker и live значения HA, но README прямо относит LVGL к
экспериментальной ветке. Установленный RC48 проверялся отдельно: `!include`
сохраняется строкой и не раскрывает файловое дерево, а `lvgl_img` показывает
placeholder. Поэтому совпадение его canvas с нашим image-heavy UI не гарантировано.

В установленной HA интеграции **Save Layout сохраняет модель проекта в HA
`.storage/esphome_designer`**, а не записывает packages/YAML в Git checkout.
Это подтверждено `storage.py` и `api/layout.py` установленной версии.
Сохранить layout, сгенерировать YAML и сохранить YAML в рабочую папку — разные
операции. Текущий проект нельзя считать синхронизированным с Git после одного Save.

Использовать его отдельно для проверки выбранной сущности/виджета или короткого
эксперимента с HA-aware макетом. Перед принятием изменений проверять diff и
нативный результат; не делать второй независимый источник всей прошивки.

## Интерактивный host + SDL в браузере: следующий возможный этап

**Не установлен и не проверен в нашей среде.** Предлагаемая схема:

```text
общий checkout read-only → ESPHome host + LVGL + SDL window
                                              │ Linux X display (Xvfb)
                                              ↓
                                       VNC server → noVNC → браузер
```

В отдельном Linux app/container нужны SDL2 development libraries, компилятор,
Xvfb, VNC server и WebSocket proxy/noVNC. SDL touchscreen передаёт мышь в LVGL.
Здесь `headless: false`: [SDL headless](https://esphome.io/components/display/sdl/)
не получает ввод, поэтому не годится для кликабельного удалённого окна.
[noVNC](https://novnc.com/info.html) переносит VNC в браузер, не интерпретирует YAML.
Размещение через HA Ingress и конкретную схему доступа ещё нужно реализовать.

Начать с mock behavior без HA. Для отдельного live-HA host entry добавить
`api:` и стабильное уникальное имя/MAC, затем вручную добавить этот host в HA
ESPHome integration по адресу, доступному **из HA**, TCP **6053**.
Автообнаружения host через mDNS не обещать; host использует сеть ОС, без `wifi:`.
Это поведение описано в [официальной host документации](https://esphome.io/components/host/).
Нынешний snapshot worker такого API не открывает и HA entities не подключает.

Для испытаний использовать отдельные HA helpers, а действия разрешить только
для тестового устройства. Это проверяет ввод и обратную связь без OTA каждого
пиксельного изменения. Физический LCD/touch и ограничения ESP32 всё равно остаются
финальной аппаратной проверкой.

## Полный пример: новая кнопка и слайдер

Пример **ещё не внедрён**: управление тестовой лампой через HA helpers
`input_boolean.panel_demo_lamp` и `input_number.panel_demo_level` (0–100).
Это отдельные сущности для разработки, а не существующее домашнее освещение.

1. **Контракт.** В общем layout добавить кнопку `ui_demo_toggle`, слайдер
   `ui_demo_level`, подпись `ui_demo_status`. Зафиксировать размеры и состояния;
   binding имён сущностей вынести в room substitutions. Комнаты разделяют
   рисунок и behavior, меняют только entity IDs/параметры.
2. **Layout.** Править YAML непосредственно либо экспортировать UI-фрагмент
   ESPboards. Сохранить в общем HA checkout и проверить Git diff.
3. **Mock behavior.** Определить `ui_demo_toggle_request` как локальное изменение
   mock state; в отдельном render script обновлять кнопку, число и подпись.
   Проверить сценарии ниже. На этом этапе нет HA API/actions.

   | Вход | Ожидаемый UI |
   |---|---|
   | off, уровень 0 | состояние off, значение 0, управление доступно |
   | on, уровень 60 | состояние on, значение 60, контраст подписи сохранён |
   | unavailable / ещё нет первого state | подпись «Нет связи», управление disabled; не изображать это как реальный 0 |
   | восстановление on / 60 | управление включено, state и число синхронизированы |

4. **Native проверка.** В mock host entry подключить те же layout/resources/events,
   затем нужный mock package. Capture-сценарий должен открыть `ui_controls`
   и снять каждый случай после LVGL flush. Workshop сейчас показывает только
   явно заданные сценарии. Проверить PNG, кириллицу, alpha, bounds и disabled style.
5. **HA input.** В live behavior читать helper state через ESPHome
   `homeassistant` sensor/text_sensor/binary_sensor и подавать его в тот же render
   script. Availability хранить отдельно от значения; обновлять также при потере
   связи, а не только после очередного числового события. Не менять UI через
   optimistic toggle без согласованной политики подтверждения.
6. **HA action.** Live реализация script ID отправляет запрос; состояние UI
   подтверждается входным helper state. Пример только кнопочной части:

   ```yaml
   script:
     - id: ui_demo_toggle_request
       then:
         - homeassistant.action:
             action: input_boolean.toggle
             data:
               entity_id: ${ha_demo_lamp_entity}
   ```

   Для завершённого значения слайдера — `input_number.set_value` с `entity_id`
   и `value`. Проверить данные через HA Developer Tools → Actions; разрешить
   тестовому ESPHome устройству выполнять HA actions. Это требование
   [Native API](https://esphome.io/components/api/#homeassistantaction-action).
   Пример не подключать к network-free mock host без определения альтернативы.
7. **Интерактивная проверка.** В предложенном SDL/noVNC host нажать кнопку и
   перетащить слайдер: один запрос на нужное событие, подтверждение из HA,
   изменение helper из HA возвращается в UI, недоступность блокирует действия,
   reconnect восстанавливает state. Пока SDL нет, snapshot покрывает внешний
   вид, а touch/actions проверяются на тестовой панели.
8. **Firmware и финальная OTA.** Validate аппаратного target, native кадры всех
   mock states, сборка Factory/OTA BIN. OTA выполнять отдельно на выбранную
   тестовую панель, после чего проверить реальный touch, reconnect, память,
   экран и HA feedback. Workshop сам устройство не прошивает. Зафиксировать
   Git commit, профиль и результат проверки перед переносом на остальные панели.

## Другие редакторы и мосты

- [LVGL Pro](https://lvgl.io/pro) использует XML и C codegen;
  [EEZ Studio](https://www.envox.eu/eez-studio-docs/) — собственный проект/Flow
  и LVGL интеграцию; [SquareLine Studio](https://squareline.io/) — собственный
  проект с экспортом native кода. Это другие исходные модели, не прямые
  редакторы нашего ESPHome YAML. Их выбор требует отдельного pipeline.
- [SquarelineToEsphome](https://github.com/gpambrozio/SquarelineToEsphome)
  предлагает `.sqproj → YAML`, включая `--output ui.yaml --monitor` для
  наблюдения за изменениями файла. Это сторонний **непроверенный в FormaPanel**
  bridge. Автоконвертация проекта не равна автоматической проверке, сборке или
  OTA; schema/events, assets и стабильные ID сначала проверить отдельным PoC.
- [LCD Wizard ESPHome export](https://lcdwizard.com/docs/esphome) — новый
  кандидат с visual preview и simulated HA inputs. Экспорт ориентирован на
  целый YAML с сопутствующими ресурсами/файлами; это не открытие нашего checkout
  без преобразования. Автор отдельно сообщает, что HA-часть проверялась чтением
  generated C++, но не запускалась с HA. В FormaPanel не испытан.
  [Модель оплаты](https://lcdwizard.com/pricing): редактирование/preview отдельно
  от учитываемой генерации кода; условия перепроверять перед использованием.

Для нашей задачи сначала улучшать существующий YAML → native цикл и сохранить
один источник истины в Git. Следующий функциональный PoC — интерактивный SDL host
с mock states, затем тестовый HA round-trip. Визуальный layout editor можно
подключать независимо, с чёткой границей generated-фрагмента и behavior.
