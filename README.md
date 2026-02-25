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

## Запуск 24/7 Бота

Теперь проект превратился в полноценную автономную систему.

1. Установите зависимости:
```bash
pip install sqlalchemy aiogram apscheduler aiohttp pysocks telethon python-dotenv beautifulsoup4 requests
```
2. Запустите бота:
```bash
python bot.py
```
*Бот автоматически скачает нужную версию Xray-core при первом запуске.*

### Возможности бота:
- **Автоматика**: Каждые 6 часов бот сам парсит, фильтрует и проверяет ключи.
- **Smart Discovery**: Бот постоянно ищет новые источники на GitHub.
- **Команды**:
    - `/parsing` — запустить цикл проверки вручную.
    - `/get_working` — получить файл с работающими Reality ключами.

## Структура проекта
- `bot.py` — Главный файл управления.
- `database.py` — Работа с базой данных SQLite.
- `modules/discovery.py` — Умный поиск новых источников.
- `main.py`, `filter_reality.py`, `verify_working.py` — Ядро парсинга.
