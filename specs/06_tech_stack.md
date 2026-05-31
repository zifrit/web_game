# 06. Tech Stack Specification

## 1. Backend

```text
Django
Django REST Framework
PostgreSQL
Redis
Celery
Celery Beat
SimpleJWT
```

## 2. Why Django

Django выбран из-за:

- сильной встроенной админки;
- удобной ORM;
- быстрого создания CRUD;
- хорошего соответствия проекту с большим количеством игровых конфигов;
- возможности быстро балансить игру через Django Admin.

## 3. PostgreSQL

Основная БД.

Хранит:

- users;
- characters;
- dungeons;
- runs;
- items;
- configs;
- claims;
- transactions.

JSON-поля допустимы для:

- growth_profile;
- possible_stats;
- generated item stats;
- items_reward draft.

## 4. Redis

Использование:

- Celery broker/result backend;
- кеширование игровых конфигов;
- кеширование leaderboard в будущем;
- временные данные, если потребуется.

## 5. Celery + Celery Beat

Использование:

- периодическое завершение походов;
- cleanup задач;
- возможные будущие фоновые игровые события.

Проверка завершения походов гибридная:

```text
1. Celery Beat периодически проверяет IN_PROGRESS runs.
2. При заходе пользователя на страницу также проверяется конкретный active run.
```

Важно: завершение похода должно быть идемпотентным.

## 6. Auth

```text
SimpleJWT
access token
refresh token
refresh rotation
```

Пароли:

```text
bcrypt или argon2
```

## 7. Media storage

Для MVP локально можно использовать Django media storage.

Для нормального окружения:

```text
S3-compatible storage
```

Варианты:

```text
MinIO local
Cloudflare R2
AWS S3
```

## 8. Frontend

```text
Next.js
React
TypeScript
Tailwind CSS
TanStack Query
React Hook Form
Zod
Zustand optional
```

## 9. Deploy MVP

Рекомендуемый MVP deploy:

```text
Docker Compose
```

Сервисы:

```text
backend
frontend
postgres
redis
celery_worker
celery_beat
nginx optional
```

## 10. Что не использовать в MVP

```text
Kubernetes
microservices
Kafka
CQRS
event sourcing
websocket-heavy architecture
custom admin frontend
```

Это лишнее для текущего масштаба.
