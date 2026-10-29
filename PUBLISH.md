# Публикация FormaPanel на GitHub

Состояние: локальный репозиторий и Git bundle **созданы**, удалённый `exceptioncpp/FormaPanel` не создан: коннектор GitHub в данной сессии не поддерживает операцию создания репозиториев.

## Вариант A: из ZIP

1. Открыть https://github.com/new и создать **пустой** репозиторий `FormaPanel` под `exceptioncpp`. Рекомендуемый начальный режим — **Private** до выбора лицензии и аудита assets. Не добавлять README/.gitignore/license при создании: они уже включены.
2. Распаковать `FormaPanel-bootstrap.zip`, зайти в каталог `FormaPanel`.
3. Выполнить:

```bash
git init -b main
git add .
git commit -m "bootstrap: FormaPanel project documentation and design pipeline"
git remote add origin git@github.com:exceptioncpp/FormaPanel.git
git push -u origin main
```

Если SSH-ключ GitHub не настроен, заменить `git@github.com:exceptioncpp/FormaPanel.git` на `https://github.com/exceptioncpp/FormaPanel.git` (понадобится поддерживаемый метод аутентификации Git).

## Вариант B: из Git bundle (история сохранена)

При наличии `FormaPanel.git.bundle`:

```bash
git clone FormaPanel.git.bundle FormaPanel
cd FormaPanel
git remote rename origin bootstrap-bundle
git remote add origin git@github.com:exceptioncpp/FormaPanel.git
git push -u origin main
```

Bundle содержит два локальных коммита и исходные файлы. Убедиться, что новый репозиторий на GitHub создан пустым.

## Smoke checks

```bash
python -m pip install -r tools/requirements.txt
python tools/render_assets.py --all
python tools/validate.py
python -m unittest discover -s tests -v
```

В репозитории **нет** заводского Guition ZIP, API ключей QWeather/HA, Wi-Fi passwords, чужих PNG/шрифтов. Лицензия FormaPanel ещё не назначена.
