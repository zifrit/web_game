# TOTP Flow And API Calls

Документ описывает, какие ручки вызываются при работе с TOTP-защитой, что фронт
передаёт в backend, что получает обратно и как меняется состояние пользователя.

## Основные сущности

### `UserTwoFactor`

Для каждого пользователя создаётся запись `UserTwoFactor`.

Ключевые поля:

- `totp_protection` - включена ли TOTP-защита для входа.
- `active_secret_ciphertext` - зашифрованный активный TOTP-secret, который уже
  подтверждён кодом и используется при входе.
- `pending_secret_ciphertext` - зашифрованный временный TOTP-secret, который
  создан на этапе setup, но ещё не подтверждён кодом.
- `pending_started_at` - время начала setup flow.
- `confirmed_at` - время успешного включения TOTP.
- `last_verified_at` - время последней успешной проверки активного TOTP-кода.
- `last_timecode` - последний использованный TOTP timecode; нужен, чтобы
  отклонять повторное использование того же кода.

Секреты не хранятся в открытом виде. Они шифруются через ключ из настройки
`TOTP_ENCRYPTION_KEY`.

## Frontend API Methods

Фронт вызывает эти методы из `frontend/lib/api.ts`:

- `api.twoFactorStatus()` -> `GET /api/auth/two-factor`
- `api.startTwoFactorSetup()` -> `POST /api/auth/two-factor/setup`
- `api.confirmTwoFactorSetup(code)` -> `POST /api/auth/two-factor/confirm`
- `api.disableTwoFactor(password, code)` -> `POST /api/auth/two-factor/disable`
- `api.login(email, password)` -> `POST /api/auth/login`
- `api.verifyLoginTotp(challengeToken, code)` -> `POST /api/auth/login/totp`

## Проверка статуса TOTP

### Когда вызывается

На экране настроек `SettingsScreen` вызывается `api.twoFactorStatus()`, чтобы
понять, включена ли защита и есть ли незавершённый setup.

### Request

```http
GET /api/auth/two-factor
Authorization: Bearer <access_token>
```

Body не передаётся.

### Response

```json
{
  "totp_protection": false,
  "setup_pending": false
}
```

Поля:

- `totp_protection` - `true`, если пользователь уже подтвердил TOTP и защита
  включена.
- `setup_pending` - `true`, если pending secret создан, но ещё не подтверждён.

## Включение TOTP: setup

### Когда вызывается

Пользователь включает тумблер TOTP на экране настроек. Фронт вызывает
`api.startTwoFactorSetup()`.

### Request

```http
POST /api/auth/two-factor/setup
Authorization: Bearer <access_token>
```

Body не передаётся.

### Что делает backend

1. Находит или создаёт `UserTwoFactor` для текущего пользователя.
2. Если `totp_protection=true`, возвращает ошибку: защита уже включена.
3. Генерирует новый TOTP-secret.
4. Создаёт `otpauth_uri` для приложения-аутентификатора.
5. Генерирует QR-картинку как data URL.
6. Сохраняет secret в `pending_secret_ciphertext`.
7. Ставит `pending_started_at`.
8. Не включает `totp_protection` до подтверждения кода.

### Response

```json
{
  "secret": "BASE32SECRET",
  "otpauth_uri": "otpauth://totp/...",
  "qr_data_url": "data:image/png;base64,..."
}
```

Фронт показывает QR-код и manual key пользователю.

## Включение TOTP: confirm

### Когда вызывается

После setup пользователь сканирует QR-код в приложении-аутентификаторе и вводит
6-значный код. Фронт вызывает `api.confirmTwoFactorSetup(code)`.

### Request

```http
POST /api/auth/two-factor/confirm
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "code": "123456"
}
```

### Что делает backend

1. Проверяет формат поля `code`.
2. В транзакции берёт `UserTwoFactor` с row lock.
3. Проверяет, что есть `pending_secret_ciphertext`.
4. Расшифровывает pending secret.
5. Проверяет TOTP-код по pending secret.
6. Если код верный:
   - переносит pending secret в `active_secret_ciphertext`;
   - очищает `pending_secret_ciphertext`;
   - очищает `pending_started_at`;
   - ставит `totp_protection=true`;
   - ставит `confirmed_at`;
   - сбрасывает `last_timecode`.

### Success response

```json
{
  "totp_protection": true,
  "setup_pending": false
}
```

После успешного ответа фронт:

1. Закрывает setup UI.
2. Обновляет кеш `["me"]` и `["twoFactor"]`.
3. Показывает toast: `TOTP-защита включена.`

### Error response

Пример неверного кода:

```json
{
  "detail": "Invalid two-factor code."
}
```

Фронт показывает inline error и toast с текстом ошибки.

## Обычный login без TOTP

### Когда вызывается

Пользователь вводит email и пароль на экране входа. Фронт вызывает
`api.login(email, password)`.

### Request

```http
POST /api/auth/login
Content-Type: application/json
```

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

### Response, если TOTP выключен

```json
{
  "access_token": "<jwt_access>",
  "refresh_token": "<jwt_refresh>",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "has_character": true,
    "avatar": null,
    "two_factor": {
      "totp_protection": false
    }
  }
}
```

Фронт сразу вызывает `setSession(...)` и пользователь авторизован.

## Login с включённым TOTP

### Первый шаг: пароль

Фронт вызывает ту же ручку:

```http
POST /api/auth/login
Content-Type: application/json
```

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

### Response, если `totp_protection=true`

```json
{
  "two_factor_required": true,
  "challenge_token": "<signed_short_lived_token>"
}
```

Важно: на этом шаге backend не выдаёт JWT-токены. Фронт сохраняет
`challenge_token` во внутреннем состоянии `AuthScreen` и показывает форму ввода
TOTP-кода.

### Второй шаг: TOTP-код

Фронт вызывает `api.verifyLoginTotp(challengeToken, code)`.

```http
POST /api/auth/login/totp
Content-Type: application/json
```

```json
{
  "challenge_token": "<signed_short_lived_token>",
  "code": "123456"
}
```

### Что делает backend

1. Проверяет подпись и срок жизни `challenge_token`.
2. Находит пользователя из challenge.
3. В транзакции берёт `UserTwoFactor` с row lock.
4. Проверяет, что TOTP-защита включена и есть active secret.
5. Расшифровывает active secret.
6. Проверяет TOTP-код.
7. Проверяет `last_timecode`, чтобы тот же код нельзя было использовать дважды.
8. При успехе обновляет `last_verified_at` и `last_timecode`.
9. Возвращает обычный auth response с JWT-токенами.

### Success response

```json
{
  "access_token": "<jwt_access>",
  "refresh_token": "<jwt_refresh>",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "has_character": true,
    "avatar": null,
    "two_factor": {
      "totp_protection": true
    }
  }
}
```

Фронт вызывает `setSession(...)`, как при обычном login.

### Error response

Неверный или повторно использованный код:

```json
{
  "detail": "Invalid two-factor code."
}
```

Невалидный или истёкший challenge:

```json
{
  "detail": "Invalid two-factor challenge."
}
```

## Отключение TOTP

### Когда вызывается

Пользователь выключает тумблер TOTP на экране настроек. Фронт открывает форму,
где нужно ввести текущий пароль и текущий TOTP-код. После подтверждения вызывает
`api.disableTwoFactor(password, code)`.

### Request

```http
POST /api/auth/two-factor/disable
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "password": "password",
  "code": "123456"
}
```

### Что делает backend

1. Проверяет пароль текущего пользователя через `authenticate(...)`.
2. В транзакции берёт `UserTwoFactor` с row lock.
3. Проверяет, что `totp_protection=true`.
4. Проверяет TOTP-код по active secret.
5. Если всё верно:
   - ставит `totp_protection=false`;
   - очищает active и pending secrets;
   - очищает `pending_started_at`;
   - очищает `confirmed_at`;
   - очищает `last_verified_at`;
   - очищает `last_timecode`.

### Success response

```json
{
  "totp_protection": false,
  "setup_pending": false
}
```

После успешного ответа фронт:

1. Закрывает форму отключения.
2. Очищает поля password/code.
3. Обновляет кеш `["me"]` и `["twoFactor"]`.
4. Показывает toast: `TOTP-защита выключена.`

### Error response

Неверный пароль:

```json
{
  "detail": "Invalid email or password."
}
```

Неверный TOTP-код:

```json
{
  "detail": "Invalid two-factor code."
}
```

Фронт показывает inline error и toast с текстом ошибки.

## `GET /api/auth/me`

После включения или выключения TOTP фронт инвалидирует `["me"]`, чтобы получить
актуальный payload пользователя.

### Request

```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

### Response fragment

```json
{
  "id": 1,
  "email": "user@example.com",
  "money_copper": 0,
  "has_character": true,
  "avatar": null,
  "two_factor": {
    "totp_protection": true
  }
}
```

## Полная последовательность включения защиты

1. `GET /api/auth/two-factor`
   - фронт узнаёт текущий статус.
2. Пользователь включает тумблер.
3. `POST /api/auth/two-factor/setup`
   - backend создаёт pending secret;
   - frontend получает `secret`, `otpauth_uri`, `qr_data_url`.
4. Пользователь сканирует QR или вводит manual key.
5. Пользователь вводит код из authenticator app.
6. `POST /api/auth/two-factor/confirm`
   - backend проверяет код;
   - переносит pending secret в active secret;
   - включает `totp_protection`.
7. Frontend обновляет `["me"]` и `["twoFactor"]`.
8. Frontend показывает success toast.

## Полная последовательность входа с TOTP

1. Пользователь вводит email/password.
2. `POST /api/auth/login`
3. Backend видит `totp_protection=true`.
4. Backend возвращает `two_factor_required=true` и `challenge_token`.
5. Frontend показывает форму TOTP-кода.
6. Пользователь вводит код.
7. `POST /api/auth/login/totp`
8. Backend проверяет challenge, active secret, TOTP-код и replay через
   `last_timecode`.
9. Backend возвращает JWT-токены.
10. Frontend сохраняет сессию.

## Полная последовательность отключения защиты

1. `GET /api/auth/two-factor`
   - фронт показывает включённый тумблер.
2. Пользователь выключает тумблер.
3. Frontend показывает форму password + current TOTP code.
4. `POST /api/auth/two-factor/disable`
5. Backend проверяет пароль.
6. Backend проверяет active TOTP-код.
7. Backend очищает secrets и выключает `totp_protection`.
8. Frontend обновляет `["me"]` и `["twoFactor"]`.
9. Frontend показывает success toast.
