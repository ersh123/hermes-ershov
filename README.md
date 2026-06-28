1|# self-ershov-memory
2|
3|[![CI](https://github.com/ersh123/self-ershov-memory/actions/workflows/ci.yml/badge.svg)](https://github.com/ersh123/self-ershov-memory/actions/workflows/ci.yml)
4|[![CodeQL](https://github.com/ersh123/self-ershov-memory/actions/workflows/codeql.yml/badge.svg)](https://github.com/ersh123/self-ershov-memory/actions/workflows/codeql.yml)
5|
6|Self-audit engine for Hermes operators. Анализирует диалоги с оператором → извлекает коррекции и правила → обновляет USER.md/MEMORY.md → создаёт скиллы. Ничего не применяет без проверки, не выдумывает, не удаляет.
7|
8|## Как работает
9|
10|```
11|state.db (диалоги)
12|    → find_corrections() — regex-поиск жалоб и правил
13|    → classify_topic() — keyword-based классификация
14|    → dedup — если тема уже в USER.md → пропуск
15|    → snapshot() — бэкап перед записью
16|    → apply → USER.md / MEMORY.md / skills
17|```
18|
19|- **Idempotent** — повторный прогон = 0 изменений
20|- **Dedup** — не дублирует уже известные правила
21|- **Snapshot** — `~/snapshots/` перед каждой правкой
22|- **Validation** — проверка лимитов (4000/8000 chars)
23|
24|## Установка
25|
26|```bash
27|hermes plugins install ersh123/self-ershov-memory --enable
28|```
29|
30|## Быстрый старт
31|
32|```bash
33|# Dry-run — посмотреть что изменится
34|python3 ~/.hermes/scripts/self-audit.py --dry-run --quick
35|
36|# Применить
37|python3 ~/.hermes/scripts/self-audit.py --execute --full
38|
39|# Только за 24 часа
40|python3 ~/.hermes/scripts/self-audit.py --execute --quick
41|```
42|
43|## Триггеры (ручной запуск)
44|
45|- «проанализируй мои диалоги»
46|- «проверь себя»
47|- «что я тебе говорил»
48|
49|## Cron
50|
51|| Режим | Расписание | Доставка |
52||-------|-----------|----------|
53|| Quick (24ч) | Ежедневно 22:00 KRSK | local |
54|| Full (30д) | Еженедельно Вс 20:00 KRSK | Telegram |
55|
56|## Тема → Скилл
57|
58|| Тема | Создаваемый скилл |
59||------|-------------------|
60|| vibe-coding | `vibe-coding` |
61|| opencode | `opencode-setup` |
62|| ресерч | `deep-research` |
63|| скиллы | `skill-quality` |
64|| deepseek | `deepseek-setup` |
65|
66|## CLI (legacy nightly memory — оставлено для совместимости)
67|
68|```bash
69|# Ручной nightly (если нужен)
70|ershov nightly --live-root ./live --artifact-root ./artifacts --no-llm
71|
72|# Review артефакта
73|ershov review --open ./artifacts/<id>
74|
75|# Apply вручную
76|ershov apply ./artifacts/<id> --live-root ./live --backup-root ./backups
77|
78|# Статус
79|ershov status --artifact-root ./artifacts
80|```
81|
82|## Структура репозитория
83|
84|```
85|src/hermes_dreaming/    — основной движок
86|scripts/               — self-audit.py, release-скрипты
87|docs/                  — документация
88|tests/                 — CI, fuzz, property-based
89|examples/              — quickstart fixture
90|```
91|
92|## Разработка
93|
94|```bash
95|uv sync --locked --extra dev
96|uv run --locked --extra dev pytest -q
97|```
98|
99|PR через GitHub Issues. Перед PR: `pytest -q`, `ruff check`, `git diff --check`.
100|
101|## Безопасность
102|
103|- Никаких автоматических записей в live-память
104|- Снапшоты перед каждой правкой
105|- Валидация размеров файлов
106|- Сухие прогоны перед реальными изменениями
107|