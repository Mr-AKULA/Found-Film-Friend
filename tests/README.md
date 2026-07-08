# Tests

Простые UI-тесты на Playwright + pytest для веб-версии Found Film Friend.

## Установка
```
pip install pytest playwright pytest-playwright
playwright install chromium
```

## Запуск
```
pytest -v tests/
pytest -v tests/ --headed --slowmo 500   # с видимым браузером, для отладки
```
