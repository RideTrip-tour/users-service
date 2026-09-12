[![CI Dev](https://github.com/RideTrip-tour/profiles-service/actions/workflows/ci-dev.yml/badge.svg)](https://github.com/RideTrip-tour/profiles-service/actions/workflows/ci-dev.yml)

# Profile Service

Сервис управления профилями пользователей на `FastAPI` и `SQLAlchemy Async`.

## Требования

- `Python 3.12+`
- `PostgreSQL 16+`
- `venv` или другое виртуальное окружение

## Переменные окружения

Сервис читает настройки из `.env`. Для локального запуска достаточно таких переменных:

```env
DB_PROFILE_SERVICE_HOST=127.0.0.1
DB_PROFILE_SERVICE_PORT=5432
DB_PROFILE_SERVICE_NAME=profile_db
DB_PROFILE_SERVICE_USER=platform
DB_PROFILE_SERVICE_PASS=12345
DEBUG=false
```

Важно: значение `DEBUG` должно быть булевым, например `true` или `false`.

## Локальный запуск

1. Создайте и активируйте виртуальное окружение:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Поднимите PostgreSQL и создайте базу `profile_db`.

Пример через Docker:

```bash
docker run --name profile-db \
  -e POSTGRES_DB=profile_db \
  -e POSTGRES_USER=platform \
  -e POSTGRES_PASSWORD=12345 \
  -p 5432:5432 \
  -d postgres:16
```

4. Примените миграции:

```bash
venv/bin/alembic upgrade head
```

5. Запустите сервис:

```bash
venv/bin/uvicorn main:app --reload
```

## Проверка

После запуска сервис доступен по адресам:

- `http://127.0.0.1:8000/api/profile/health`
- `http://127.0.0.1:8000/api/profile/docs`
- `http://127.0.0.1:8000/api/profile/openapi.json`

## API

Базовый префикс профилей: `/api/profile`

Базовый префикс админских ручек: `/api/admin/profile`. Они вызываются gateway из закрытой сети.

Все защищенные ручки ожидают, что в `request.state.user` уже будет положен пользователь gateway-мидлварью или внешней auth-логикой.

### `POST /api/profile/`

Создает профиль для текущего пользователя.

Тело запроса:

```json
{
  "first_name": "Ivan",
  "last_name": "Petrov",
  "phone_number": "+79990000000",
  "birth_date": "2000-01-23",
  "about_me": "Люблю путешествия",
  "activities": ["ski", "hiking"],
  "country": "Russia",
  "city": "Moscow",
  "citizenship": "RU",
  "currency": "RUB",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

Ответы:

- `201 Created` - профиль создан
- `401 Unauthorized` - пользователь не определен
- `409 Conflict` - профиль уже существует

### `GET /api/profile/me`

Возвращает профиль текущего пользователя.

Ответы:

- `200 OK` - профиль найден
- `401 Unauthorized` - пользователь не определен
- `404 Not Found` - профиль не найден

### `GET /api/profile/{user_id}`

Возвращает профиль по `user_id`, но только если `user_id` совпадает с текущим пользователем.

Ответы:

- `200 OK` - профиль найден
- `401 Unauthorized` - пользователь не определен
- `403 Forbidden` - запрошен чужой профиль
- `404 Not Found` - профиль не найден

### `PATCH /api/profile/me`

Частично обновляет профиль текущего пользователя.

Тело запроса можно передавать частично:

```json
{
  "first_name": "Ivan",
  "city": "Saint Petersburg",
  "activities": ["surfing"]
}
```

Ответы:

- `200 OK` - профиль обновлен
- `401 Unauthorized` - пользователь не определен
- `404 Not Found` - профиль не найден

### `DELETE /api/profile/{user_id}`

Удаляет профиль по `user_id`, но только если `user_id` совпадает с текущим пользователем.

Ответы:

- `204 No Content` - профиль удален
- `401 Unauthorized` - пользователь не определен
- `403 Forbidden` - попытка удалить чужой профиль
- `404 Not Found` - профиль не найден

### Формат ответа профиля

```json
{
  "id": 1,
  "user_id": 42,
  "role": "user",
  "first_name": "Ivan",
  "last_name": "Petrov",
  "phone_number": "+79990000000",
  "birth_date": "2000-01-23",
  "about_me": "Люблю путешествия",
  "activities": ["ski", "hiking"],
  "country": "Russia",
  "city": "Moscow",
  "citizenship": "RU",
  "currency": "RUB",
  "avatar_url": "https://example.com/avatar.jpg",
  "created_at": "2026-04-12T12:00:00Z",
  "updated_at": "2026-04-12T12:00:00Z"
}
```

## Идентификация устройства

Для фиксации устройств, с которых пользователь обращается к сервису, фронтенд должен передавать информацию об устройстве в HTTP-заголовках.

### Заголовки устройства

| Заголовок            | Обязательный | Описание                                         |
| -------------------- | ------------ | ------------------------------------------------ |
| `X-Device-ID`        | Да           | Уникальный и стабильный идентификатор устройства |
| `X-Device-Name`      | Нет          | Название устройства, отображаемое пользователю   |
| `Sec-CH-UA-Platform` | Нет          | Платформа устройства, например `"Windows"`       |
| `User-Agent`         | Нет          | User-Agent клиента                               |

### Пример запроса

```http
GET /api/profile/me HTTP/1.1
Host: 127.0.0.1:8000
X-Device-ID: 8f7c2a91-4d3b-4a6e-b123-123456789abc
X-Device-Name: My Laptop
Sec-CH-UA-Platform: "Windows"
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148.0.0.0 Safari/537.36
```

### Требования к `X-Device-ID`

`X-Device-ID` должен быть уникальным для каждого устройства и сохраняться между запросами.
Например, один и тот же браузер должен отправлять один и тот же `X-Device-ID`:
```http
X-Device-ID: 8f7c2a91-4d3b-4a6e-b123-123456789abc
```
При обращении с другого устройства должен использоваться другой идентификатор:
```http
X-Device-ID: 31a5c821-7f21-4c12-9876-987654321def
```
Если `X-Device-ID` не передан, устройство не регистрируется.

### Логика регистрации

При первом обращении устройства сервис создаёт запись в `profile_devices`.
При последующих обращениях `X-Device-ID` используется для определения устройства. Для снижения нагрузки на базу данных регистрация устройства дополнительно кешируется в Redis.
Информация о последнем обращении хранится в поле `last_seen_at`.


## Тесты

Установка тестовых зависимостей:

```bash
pip install -r requirements.test.txt
```

Запуск тестов:

```bash
venv/bin/pytest
```
