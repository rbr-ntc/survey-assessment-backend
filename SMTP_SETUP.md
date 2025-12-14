# Настройка SMTP для отправки email

Для работы системы регистрации и восстановления пароля необходимо настроить SMTP сервер для отправки email.

## Переменные окружения

Добавьте следующие переменные в Railway (или в `.env` для локальной разработки):

### Обязательные переменные:

```bash
SMTP_HOST=smtp.gmail.com                    # Адрес SMTP сервера
SMTP_PORT=587                                # Порт SMTP (обычно 587 для TLS, 465 для SSL)
SMTP_USER=your-email@gmail.com               # Email для авторизации на SMTP сервере
SMTP_PASSWORD=your-app-password              # Пароль или App Password для SMTP
SMTP_FROM_EMAIL=your-email@gmail.com         # Email отправителя (обычно тот же что SMTP_USER)
SMTP_FROM_NAME=LearnHub LMS                  # Имя отправителя (опционально, по умолчанию "LearnHub LMS")
```

## Настройка для популярных провайдеров

### Gmail

1. Включите двухфакторную аутентификацию в вашем Google аккаунте
2. Создайте "App Password":
   - Перейдите в [Google Account Settings](https://myaccount.google.com/)
   - Security → 2-Step Verification → App passwords
   - Создайте новый App Password для "Mail"
   - Используйте этот пароль в `SMTP_PASSWORD`

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # App Password (16 символов без пробелов)
SMTP_FROM_EMAIL=your-email@gmail.com
```

### Яндекс.Почта

```bash
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=465
SMTP_USER=your-email@yandex.ru
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=your-email@yandex.ru
```

### Mail.ru

```bash
SMTP_HOST=smtp.mail.ru
SMTP_PORT=465
SMTP_USER=your-email@mail.ru
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=your-email@mail.ru
```

### SendGrid

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_FROM_EMAIL=your-verified-sender@example.com
```

### AWS SES

```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com  # Замените на ваш регион
SMTP_PORT=587
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=your-verified-email@example.com
```

## Проверка настройки

После добавления переменных окружения:

1. Перезапустите контейнер на Railway
2. Попробуйте зарегистрироваться - код должен прийти на email
3. Если код не приходит, проверьте логи Railway на наличие ошибок SMTP

## Отладка

Если email не отправляются, проверьте логи:

```bash
# В Railway logs ищите строки:
[EmailService] Email not configured, skipping send to ...
# или
Failed to send verification email to ...
```

Если видите "Email not configured" - проверьте, что все переменные SMTP установлены.

## Безопасность

⚠️ **Важно**: Никогда не коммитьте SMTP пароли в git. Используйте только переменные окружения Railway.

## Альтернатива: Разработка без SMTP

Для локальной разработки без настройки SMTP:
- Коды верификации все равно генерируются и сохраняются в БД
- Вы можете найти код в логах или проверить БД напрямую
- Или временно отключите проверку email_verified в login endpoint

