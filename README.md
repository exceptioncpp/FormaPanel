# FormaPanel

**Interior-first smart panels powered by LVGL and Home Assistant.**

FormaPanel — проект эстетичных сенсорных панелей для умного дома. Его цель — соединить богатые возможности **LVGL**, интеграцию с **Home Assistant** и визуальный язык, благодаря которому экран становится частью интерьера, а не технической консолью.

> **Статус:** design-first research / repository bootstrap. **Рабочей прошивки FormaPanel пока нет.** Скриншоты и макеты не доказывают готовность прошивки.

## Основные идеи

- Красивый, спокойный, целостный интерфейс. Типографика, композиция и изображение важнее количества кнопок.
- Локальный Home Assistant — источник данных и исполнитель команд. Панели **не** управляют физическими исполнительными устройствами напрямую; собственных реле в используемой версии нет.
- Первая платформа: **Guition ESP32-S3-4848S040, 4″, 480×480, capacitive touch**. Будущий экспериментальный профиль: **ESP32-P4, 4″, 720×720**, конкретная ревизия платы не выбрана.
- Общая дизайн-система и кодовая база для **5 панелей**: гостиная, спальня, кабинет, ванная, прихожая.
- Векторные исходники и адаптивные макеты; сборка оптимизированных assets под разрешение и бюджет памяти каждого устройства.
- Никакой обязательной облачной инфраструктуры. Работа при недоступности HA — отдельное исследование, не часть текущего scope.

## Содержание репозитория

| Путь | Роль |
|---|---|
| [docs](docs/README.md) | Требования, исследование, дизайн-система, архитектура, roadmap, тесты |
| `ui/` | Визуальные макеты, дизайн-токены, компоненты |
| `assets/source/` | Оригинальные векторные и hi-res исходники |
| `assets/generated/` | Подготовленная графика под 480×480 и 720×720 |
| `firmware/esphome/` | Целевая ESPHome + LVGL реализация |
| `firmware/native/` | Исследуемый native ESP-IDF + LVGL конкурент ESPHome (пока без рабочей прошивки) |
| `config/ha/` | Пример контракта/привязок HA, без secrets |
| `hardware/` | Аппаратные профили и результаты измерений |
| `tools/` | Рендер, инвентаризация архивов, проверки |
| `tests/` | Автоматические и ручные проверки |
| `references/` | Ссылки на исследования и изображения; не копии чужих ресурсов |
| `third_party/` | Манифест сторонних зависимостей и лицензий; без заводского SDK |

## Старт работы с визуальными ресурсами

```bash
python -m pip install -r tools/requirements.txt
python tools/render_assets.py --all
python -m unittest discover -s tests -v
```

Результат: PNG preview для 480 и 720. Демонстрационный SVG — **оригинальный эскиз FormaPanel**, не заводская тема Guition. Генератор не прошивает устройство.

## Исследование прошивки и UI preview (октябрь 2026)

- [Базы прошивки: ESPHome + LVGL 9, native ESP-IDF, готовые проекты, P4](docs/02-research/firmware-platforms-2026-10.md)
- [Визуальные инструменты: ESPBoards, ESPHomeDesigner, ESPHome-LVGL-Simulator, LVGL Pro, EEZ, SquareLine, SDL](docs/02-research/lvgl-visual-tools-2026-10.md)
- [Windows 11 workflow, компиляция и схема GitHub Actions](docs/02-research/build-preview-workflows.md)
- [Реестр источников и границы подтверждения](docs/02-research/research-source-register-2026-10.md)
- [План RH-01/LA-01 сравнения на реальном Guition](docs/06-validation/rh01-platform-ab-test.md), [ADR-0003 о критериях выбора](docs/04-architecture/adr/0003-platform-evaluation.md)

**Выбор не окончательный:** ESPHome — первичный S3 baseline, native IDF — обязательный для оценки candidate. Никаких firmware benchmark или on-device результатов пока нет. Новые материалы — документы, без внедрения новой прошивки или CI job.

## Проектные решения

- [Требования и границы](docs/01-requirements/requirements.md)
- [Функции пяти панелей](docs/01-requirements/rooms.md)
- [Индекс исследования](docs/02-research/references.md)
- [Разбор заводского Guition](docs/02-research/guition-factory-demo.md)
- [Дизайн-система](docs/03-design/design-system.md)
- [Hi-res и адаптивность 480/720](docs/03-design/resolution-strategy.md)
- [Архитектура](docs/04-architecture/architecture.md)
- [План и критерии готовности](docs/05-roadmap/roadmap.md)

**Примечание по интеллектуальной собственности:** заводской архив Guition, графика, сторонние шрифты и скриншоты не входят в репозиторий. Подлинная лицензия каждого источника должна быть проверена до переноса. Лицензия самого FormaPanel пока не выбрана.
