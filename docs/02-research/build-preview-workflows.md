# Сборка, предпросмотр и CI: состояние и направления

Обновлено **01.11.2026**. Этот документ заменяет первоначальный proposal
29.10.2026 с несуществовавшими тогда entry и Windows SDK. Текущий процесс
описан в [операционном руководстве](../06-validation/build-and-preview-runbook.md),
а файлы и правила включения — в [компоновке исходников](../04-architecture/source-composition.md).

## Действующий baseline

- Firmware: ESPHome **2026.10.1**, LVGL **9.5.0**, ESP-IDF **5.5.6**.
- Сервер сборки: Home Assistant, pinned официальный ESPHome build image.
- Браузерные инструменты: Studio Code Server и FormaPanel Workshop **0.1.1**.
- Один Git checkout, доступный редактору и read-only сборщику.
- Результаты: native LVGL PNG, Factory/OTA BIN и журналы в private data Workshop.
- На Windows **не устанавливаются ESP-IDF, CMake, Ninja, PlatformIO или SDL SDK**.

Файлы ESPHome уже существуют: базовый `formapanel-rh01.yaml`, две цели
`targets/living.yaml` и `targets/bedroom.yaml`, общие packages, room profiles
и host previews. Их пары перечисляет `config/workbench-targets.json`.
Не использовать прежние примерные `panels/living-rh01.yaml` и версию
2026.10.0 как действующие инструкции.

## Один UI для device и preview

```text
общие packages + room profile + assets
                │
     ┌──────────┴───────────┐
     ↓                      ↓
ESP32 target             host preview
hardware/connection      snapshot backend
     ↓                      ↓
Factory / OTA BIN        настоящий LVGL PNG
```

ESPHome раскрывает настоящие `packages`/`!include`; Workshop не поддерживает
вторую вручную редактируемую копию UI. Гостиная и спальня подключают один
профиль к обеим своим целям. Базовый RH-01 — фиксированный эталон: его host
entry отдельно задаёт demo substitutions; правка значения только в device
entry не меняет host demo. Общий `rh01-ui.yaml` используется в обоих случаях.

Для visual authoring допускается отдельный generated UI-фрагмент; ручные
bindings и HA scripts хранятся снаружи. Полный процесс и ограничения редакторов:
[методология UI](effective-ui-development-2026-11.md).

## Практическая итерация

1. Сохранить YAML/PNG/TTF в общем checkout из Studio Code Server.
2. Выбрать профиль в Workshop, выполнить Validate либо native preview.
3. Проверить необходимые страницы и состояния. Новые страницы надо явно
   добавить в capture-сценарий: текущий backend автоматически их не обходит.
4. После принятия визуального результата собрать firmware BIN.
5. Проверить и установить на выбранную панель отдельным USB/OTA действием.
   Успешный host render не подтверждает GPIO/timings/touch/PSRAM.

В 0.1.1 wrappers и ESPHome metadata имеют постоянные пути, а snapshots
уникальны для job. Проверенный простой layout edit занимает 7.88 с серверного
задания; это не гарантия для других assets/конфигураций. [Замеры](../06-validation/ha-workshop-incremental-2026-11-01.md).
Автозапуск после Save и интерактивный SDL/noVNC не внедрены.

## Windows: только лёгкие проверки и дополнительный preview

Git и браузер достаточны для основного процесса в HA. Для локальной работы
с assets достаточно Python и библиотек `tools/requirements.txt`:

```powershell
python -m pip install -r tools/requirements.txt
python tools/render_assets.py --all
python tools/render_rh01.py
python tools/validate.py
python -m unittest discover -s tests -v
```

Отдельный `python tools/preview_rh01.py` открывает RH-01 через адаптированный
JS simulator на loopback 8080. Это приблизительный одностраничный preview,
не универсальное раскрытие packages и не runtime HA. Он не заменяет native
кадры и не является обязательным этапом.

## Что выполняет GitHub Actions

Действующий [verify.yml](../../.github/workflows/verify.yml) описывает один job:

- Python 3.12 на Ubuntu и зависимости asset pipeline;
- render базовых SVG и RH-01 ресурсов;
- `tools/validate.py`;
- `unittest discover`.

В нём **нет** ESPHome config/compile, native render, firmware artifacts или
OTA. Наличие workflow не означает, что текущие незакоммиченные изменения
уже отправлены на GitHub или remote checks запускались на этом working tree.

Будущий firmware CI должен выбирать реальные targets из manifest,
использовать согласованный pinned toolchain и тестовые provisioning values,
сохранять manifest и результаты отдельно от production credentials.
Добавлять такой job только после его фактического green run; не выдавать
шаблон CI за установленную сборочную среду.

## Native ESP-IDF и интерактивный host — разные направления

`firmware/native/` остаётся исследовательским кандидатом без рабочей прошивки.
LVGL Pro/EEZ/SquareLine с C/XML требуют отдельного pipeline либо проверенного
моста; проект не поддерживает автоматически вторую production UI-реализацию.

Для интерактивного просмотра **существующего ESPHome YAML** переход на native C
не нужен: официальный ESPHome host + SDL — возможное расширение. Для браузера
предлагаются Linux graphical session и VNC/noVNC. Такие зависимости размещаются
на HA/отдельном сервере или в Docker, не на Windows. Это пока предложение,
а не работающая часть Workshop.

## Состояние проверок

| Проверка | Факт |
|---|---|
| Assets/alpha и server regression tests | 11 локальных тестов проходят; workflow настроен на их запуск |
| ESPHome config и ESP32 compile | Проверены на HA, отчёты в `docs/06-validation/` |
| Native ESPHome LVGL snapshot | Проверен на HA; не требует SDL |
| ESP-IDF native C/UI branch | Не реализована |
| Автоматический firmware/native CI | Не реализован |
| Реальный Guition LCD/touch/HA/OTA и soak | Ожидают аппаратной приёмки |
| Пять различных комнатных прошивок | Есть базовый RH-01 и два demo профиля; остальные ещё не созданы |
| P4 720 | Плата не выбрана; только assets/research |

Точные доказательства и границы: [план проверок](../06-validation/test-plan.md),
[первый Compile](../06-validation/rh01-build-2026-10-29.md),
[Workshop](../06-validation/ha-workshop-2026-10-31.md).
