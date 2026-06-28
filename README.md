# hermes-ershov

[![CI](https://github.com/ersh123/hermes-ershov/actions/workflows/ci.yml/badge.svg)](https://github.com/ersh123/hermes-ershov/actions/workflows/ci.yml)
[![CodeQL](https://github.com/ersh123/hermes-ershov/actions/workflows/codeql.yml/badge.svg)](https://github.com/ersh123/hermes-ershov/actions/workflows/codeql.yml)

Self-audit engine for Hermes operators. Анализирует диалоги с оператором → извлекает коррекции и правила → обновляет USER.md/MEMORY.md → создаёт скиллы. Ничего не применяет без проверки, не выдумывает, не удаляет.

## Как работает

```
state.db (диалоги)
    → find_corrections() — regex-поиск жалоб и правил
    → classify_topic() — keyword-based классификация
    → dedup — если тема уже в USER.md → пропуск
    → snapshot() — бэкап перед записью
    → apply → USER.md / MEMORY.md / skills
```

- **Idempotent** — повторный прогон = 0 изменений
- **Dedup** — не дублирует уже известные правила
- **Snapshot** — `~/snapshots/` перед каждой правкой
- **Validation** — проверка лимитов (4000/8000 chars)

## Установка

```bash
hermes plugins install ersh123/hermes-ershov --enable
```

## Быстрый старт

```bash
# Dry-run — посмотреть что изменится
python3 ~/.hermes/scripts/self-audit.py --dry-run --quick

# Применить
python3 ~/.hermes/scripts/self-audit.py --execute --full

# Только за 24 часа
python3 ~/.hermes/scripts/self-audit.py --execute --quick
```

## Триггеры (ручной запуск)

- «проанализируй мои диалоги»
- «проверь себя»
- «что я тебе говорил»

## Cron

| Режим | Расписание | Доставка |
|-------|-----------|----------|
| Quick (24ч) | Ежедневно 22:00 KRSK | local |
| Full (30д) | Еженедельно Вс 20:00 KRSK | Telegram |

## Тема → Скилл

| Тема | Создаваемый скилл |
|------|-------------------|
| vibe-coding | `vibe-coding` |
| opencode | `opencode-setup` |
| ресерч | `deep-research` |
| скиллы | `skill-quality` |
| deepseek | `deepseek-setup` |

## CLI (legacy nightly memory — оставлено для совместимости)

```bash
# Ручной nightly (если нужен)
ershov nightly --live-root ./live --artifact-root ./artifacts --no-llm

# Review артефакта
ershov review --open ./artifacts/<id>

# Apply вручную
ershov apply ./artifacts/<id> --live-root ./live --backup-root ./backups

# Статус
ershov status --artifact-root ./artifacts
```

## Структура репозитория

```
src/hermes_dreaming/    — основной движок
scripts/               — self-audit.py, release-скрипты
docs/                  — документация
tests/                 — CI, fuzz, property-based
examples/              — quickstart fixture
```

## Разработка

```bash
uv sync --locked --extra dev
uv run --locked --extra dev pytest -q
```

PR через GitHub Issues. Перед PR: `pytest -q`, `ruff check`, `git diff --check`.

## Безопасность

- Никаких автоматических записей в live-память
- Снапшоты перед каждой правкой
- Валидация размеров файлов
- Сухие прогоны перед реальными изменениями
