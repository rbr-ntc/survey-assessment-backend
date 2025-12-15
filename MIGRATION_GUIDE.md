# 🚀 Инструкция по миграции

Для запуска новой универсальной системы тестов нужно выполнить две миграции:

## 1. PostgreSQL: Создание таблицы `quiz_attempts`

Миграция Alembic запускается автоматически при старте контейнера через `start.sh`.

### Вручную (локально):

```bash
cd survey-assessment-backend
alembic upgrade head
```

### На Railway:

Миграция запустится автоматически при деплое (через `start.sh`).

---

## 2. MongoDB: Создание `quiz_content` документа

Нужно запустить скрипт миграции для создания документа с конфигурацией теста.

### Локально:

```bash
cd survey-assessment-backend
python scripts/migrate_quiz_content.py
```

### В Docker контейнере:

```bash
docker exec -it <container_name> python scripts/migrate_quiz_content.py
```

### На Railway:

1. **Вариант 1: Через Railway CLI**
   ```bash
   railway run python scripts/migrate_quiz_content.py
   ```

2. **Вариант 2: Через временный скрипт в start.sh** (добавить один раз)
   ```bash
   # В start.sh после миграций Alembic добавить:
   if [ -n "${MONGO_URL:-}" ]; then
     echo "[start] running MongoDB quiz migration..."
     python scripts/migrate_quiz_content.py || echo "[start] MongoDB migration failed or already done"
   fi
   ```

3. **Вариант 3: Вручную через Railway Shell**
   - Зайти в Railway Dashboard → Service → Deployments → View Logs
   - Или использовать Railway Shell (если доступен)

---

## ✅ Проверка миграций

### PostgreSQL:
```sql
-- Проверить таблицу
SELECT * FROM quiz_attempts LIMIT 1;
```

### MongoDB:
```javascript
// Проверить документ
db.quiz_content.findOne({_id: "quiz:system-analyst-assessment"})
```

---

## 🔄 Что создается:

### PostgreSQL:
- Таблица `quiz_attempts` с полями:
  - `id`, `user_id`, `quiz_id`, `status`, `score`, `level`, `passed`
  - `started_at`, `completed_at`, `time_spent_seconds`
  - `category_scores`, `strengths`, `weaknesses` (JSON)
  - `result_content_id` (ссылка на MongoDB)

### MongoDB:
- Коллекция `quiz_content` (создается автоматически)
- Документ `quiz:system-analyst-assessment` с:
  - Конфигурацией категорий из `app/utils/__init__.py`
  - Конфигурацией уровней из `app/utils/__init__.py`
  - Списком всех question_ids из коллекции `questions`
  - Настройками теста

---

## ⚠️ Важно:

1. **Миграция MongoDB идемпотентна** - можно запускать несколько раз, она проверит существование документа
2. **Миграция PostgreSQL идемпотентна** - проверяет существование таблицы перед созданием
3. После миграции старый API (`/questions`, `/results`) продолжит работать для обратной совместимости
4. Новый API доступен по `/api/v1/quizzes/*`

