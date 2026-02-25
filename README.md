# Vless Multi-Channel Parser

Модульный парсер на Python для автоматического поиска и проверки Vless-конфигураций из различных источников (GitHub, Telegram, Web).

## Структура проекта

- `main.py`: Точка входа. Запускает параллельные потоки для Premium и Free каналов.
- `config.py`: Конфигурация ресурсов, API ключей и настроек скрейпера.
- `modules/`:
  - `github_parser.py`: Скрейпинг сырых файлов с GitHub.
  - `telegram_parser.py`: Парсинг сообщений из Telegram-каналов через Telethon.
  - `web_parser.py`: Веб-скрейпинг через BeautifulSoup4.
- `utils/`:
  - `scraper.py`: Базовый класс для HTTP-запросов с ротацией User-Agent.
  - `validator.py`: Извлечение Vless через Regex и проверка доступности хоста.

## Настройка

1. **Telegram API**:
   - Перейдите на [my.telegram.org](https://my.telegram.org).
   - Залогиньтесь, выберите "API development tools".
   - Создайте приложение, чтобы получить `api_id` и `api_hash`.
2. **Environment**:
   - Данные уже внесены в `.env` (не публикуйте этот файл!).
3. **Установка зависимостей**:
   ```bash
   pip install -r requirements.txt
   ```

## Запуск (Двухэтапный процесс)

### Этап 1: Парсинг и сбор
Собирает ключи из всех источников и проверяет их доступность.
```bash
python main.py
```
Результаты: `premium_vless.txt` и `free_vless.txt`.

### Этап 2: Фильтрация Reality
Выделяет из собранных файлов только те ключи, которые поддерживают Reality.
```bash
python filter_reality.py
```
Результат: `vless-reality.txt`.

### Этап 3: Глубокая проверка (Xray-core)
Проверяет, действительно ли ключи работают и пропускают трафик.
1. Скачайте `Xray-core` для Windows с [официального репозитория](https://github.com/XTLS/Xray-core/releases).
2. Распакуйте и положите файл `xray.exe` в корень папки проекта.
3. Запустите проверку:
```bash
python verify_working.py
```
Результат: `working_vless.txt` (только 100% рабочие ключи с указанием задержки в логах).

## Безопасность

Файлы `.env` и `*.session` добавлены в `.gitignore`, чтобы предотвратить утечку учетных данных.
