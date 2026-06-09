---
name: cleanup_worktree
description: Use when removing a git worktree in okama-dash after its task branch was merged into dev — "удали worktree", "убери worktree после мерджа в dev", "remove the worktree", "git worktree remove", "уборка worktree", or any cleanup of a finished okama-dash-<task> worktree. Covers rescuing the worktree's non-synced project memory FIRST, then the safe removal.
---

# Уборка worktree после мерджа в dev (okama-dash)

Задача в okama-dash иногда разрабатывается в выделенном git worktree (например,
`okama-dash-macro`). Когда ветка задачи **смерджена в `dev`**, worktree удаляется
вместе с локальной директорией — не оставляй отработавшие worktree висеть. Но
**сначала спаси проектную память worktree**, иначе она теряется.

## Почему память worktree теряется (главный риск)

Память сессии Claude Code привязана к namespace из абсолютного `cwd` (`/`→`-`).
У worktree `cwd` **другой**, чем у главного checkout, поэтому и namespace другой:

- **Главный checkout:** `~/.claude/projects/-home-…-okama-dash/memory` — это
  симлинк на синкаемый `~/claude/memory/okama-dash` (мирроится ноут ↔ claw).
- **Worktree:** пишет память в **свой** namespace
  `~/.claude/projects/-home-…-okama-dash-<task>/memory/` — отдельную, **не**
  синкаемую директорию, которой нет в репозитории `~/claude`.

При мердже ветки worktree в `dev` эту память легко потерять: она не в синкаемом
месте, а worktree вот-вот удалят.

## Процедура

### 1. Спаси память worktree (ПЕРЕД удалением)

```bash
# namespace = abs-путь worktree с '/' → '-'
ls ~/.claude/projects/-home-…-okama-dash-<task>/memory/
```

Если сессия worktree писала память — перенеси новые/обновлённые файлы в синкаемую
`~/claude/memory/okama-dash/`, **сверяясь с уже лежащими там** (не затирай более
свежие записи вслепую), обнови `MEMORY.md`-указатели, затем закоммить и запушь
`~/claude` (глобальное правило `claude_repo_auto_commit`).

### 2. Удали worktree

Запускай **из другой директории**, не изнутри удаляемого worktree (иначе твой
текущий каталог окажется снесён):

```bash
git worktree remove /path/to/okama-dash-<task>
```

- `git worktree remove` сносит и регистрацию worktree (в `.git/worktrees/`), и
  саму рабочую директорию за один шаг. **Не** удаляй директорию вручную
  (`rm -rf`) — останется висящая регистрация, требующая `git worktree prune`.
- Команда **откажется**, если в дереве есть незакоммиченные или неотслеживаемые
  файлы (документированное поведение git — предохранитель от потери работы).
  Сначала убедись, что всё нужное закоммичено/перенесено, и только тогда удаляй
  (при осознанной необходимости — `--force`, но это сознательный риск).

### 3. (Опционально) удали ветку

Удаление worktree само по себе **не** удаляет ветку. Ветка уже в `dev`, так что
локальную ветку задачи можно убрать отдельно, если она больше не нужна:

```bash
git branch -d <task>
```

## Checklist

- [ ] Проверил namespace памяти worktree (`ls …-okama-dash-<task>/memory/`)
- [ ] Перенёс новую память в `~/claude/memory/okama-dash/` (не затёр свежее), обновил `MEMORY.md`, закоммитил+запушил `~/claude`
- [ ] `git worktree remove` запущен из другой директории (не изнутри worktree)
- [ ] Не использовал `rm -rf` на директории worktree
- [ ] (При необходимости) удалил локальную ветку задачи
