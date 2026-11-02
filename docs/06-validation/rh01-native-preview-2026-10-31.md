# RH-01: настоящий LVGL preview на HA, 2026-10-31

Проверен native build **ESPHome 2026.10.1 / LVGL 9.5.0** с официальными `host` и
`display: snapshot`. Сборка использует тот же многофайловый
`firmware/esphome/packages/rh01-ui.yaml`, изображения и Nunito TTF, что и
прошивка ESP32. Это изображение из framebuffer LVGL, а не браузерная имитация.

## Результат

- `esphome config`: успешно.
- `esphome compile`: успешно; первый native build прошёл 571 шаг Ninja.
- Программа запущена в существующем HA Device Builder; получила два BMP
  **480×480**, состояния лампы on/off. Затем завершён только native процесс.
- Финальная инкрементальная сборка и повторный запуск также успешны;
  журнал содержит `RH01_NATIVE_PREVIEW_COMPLETE` на уровне INFO.
- BMP загружены на Windows с проверкой SHA-256 относительно HA,
  преобразованы без потерь в PNG и визуально проверены.
- Различия двух состояний ограничены лампой: bounding box
  **`(386, 364)–(458, 435)`**, координаты Pillow с исключёнными правым/нижним краями.
- Образ ESP32, Wi-Fi/API/OTA и существующие HA приложения не изменялись.
  Прошивка устройства и перезапуск HA не выполнялись.

Для Linux уже были доступны GCC, G++ и Ninja. Установка SDL2, SDK на Windows
или дополнительных HA приложений не понадобилась.

SHA-256 общего UI-пакета:
`c4a86595045dd10d97fac02b2ab728a55aeba6d0542683436bdebefe624f73fc`.
Ресурсы при доставке также сверены с исходниками.

## Расположение

Репозиторный профиль: [`host-rh01.yaml`](../../firmware/esphome/previews/host-rh01.yaml).
На HA используется отдельный wrapper:

```yaml
substitutions:
  formapanel_asset_dir: /config/esphome/formapanel-rh01/assets
  preview_build_path: /data/build/formapanel-rh01-host
packages:
  preview: !include ../firmware/esphome/previews/host-rh01.yaml
esphome:
  name: formapanel-rh01-host
```

Wrapper находится в `/config/esphome/formapanel-rh01/previews/native.yaml`.
Исполняемый файл:
`/data/build/formapanel-rh01-host/.pioenvs/formapanel-rh01-host/program`.
Профиль не содержит секретов, сетевых интерфейсов и ESP32 hardware-конфигурации.

В запуске сборки убирается `ESPHOME_IS_HA_ADDON`, задаются
`ESPHOME_DATA_DIR=/config/esphome/formapanel-rh01/native-data` и
`ESPHOME_HOST_PREFIX=/data/cache/host`. При запуске программы
`ESPHOME_SNAPSHOT_DIR` указывает на новый подкаталог
`/config/esphome/formapanel-rh01/native-output/<timestamp>`.
Отдельный каталог необходим: snapshot не перезаписывает существующие файлы.

Локальный приватный помощник:

```powershell
python reports/local/native_preview_ha.py deploy
python reports/local/native_preview_ha.py build
python reports/local/native_preview_ha.py fetch
```

Результаты: `reports/local/native-preview/rh01-on.png`, `rh01-off.png`,
исходные BMP, `config.log`, `compile.log`, `runtime.log`,
`manifest.json` и `hashes.json`. Каталог игнорируется Git.
Статическую публикацию в HA выполняет отдельный viewer; native процесс
не остаётся сервером и не открывает сетевых портов.

## Что проверка подтверждает

Общий YAML/UI успешно компилируется и рисуется настоящим LVGL на Linux,
PNG/RGB565/alpha и локальные шрифты проходят штатные ESPHome converters.
Смена изображения лампы работает в общем UI-пакете.

Это не проверка физического LCD, калибровки touch, USB, PSRAM,
таймингов дисплея, Wi-Fi/API, runtime памяти ESP32 или работы OTA.
Headless capture не является браузерным визуальным редактором.
