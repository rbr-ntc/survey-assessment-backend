"""
Email service for sending verification codes, password reset, and welcome emails.
Uses aiosmtplib for async email sending and Jinja2 for HTML templates.
"""
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import settings


class EmailService:
    """Service for sending emails with HTML templates"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send email with HTML and optional text body.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Optional plain text body
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.smtp_host or not self.smtp_user:
            # Email not configured, log and return False
            print(f"[EmailService] Email not configured, skipping send to {to_email}")
            return False

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject

            # Add text and HTML parts
            if text_body:
                message.attach(MIMEText(text_body, "plain"))
            message.attach(MIMEText(html_body, "html"))

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=True,
            )

            print(f"[EmailService] Email sent successfully to {to_email}")
            return True

        except Exception as e:
            print(f"[EmailService] Error sending email to {to_email}: {e}")
            return False

    def render_verification_code_template(self, code: str, user_name: str) -> str:
        """
        Render HTML template for email verification code.
        
        Args:
            code: 6-digit verification code
            user_name: User's name
            
        Returns:
            HTML email body
        """
        return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Код подтверждения</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 32px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .code-container {{
            background: rgba(102, 126, 234, 0.1);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(102, 126, 234, 0.3);
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            margin: 30px 0;
        }}
        .code {{
            font-size: 48px;
            font-weight: bold;
            letter-spacing: 8px;
            color: #667eea;
            font-family: 'Courier New', monospace;
        }}
        .message {{
            color: #333;
            line-height: 1.6;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">LearnHub LMS</div>
        </div>
        
        <h1 style="color: #333; text-align: center;">Подтверждение email</h1>
        
        <p class="message">
            Здравствуйте, <strong>{user_name}</strong>!
        </p>
        
        <p class="message">
            Для подтверждения вашего email адреса используйте следующий код:
        </p>
        
        <div class="code-container">
            <div class="code">{code}</div>
        </div>
        
        <p class="message" style="text-align: center; color: #666; font-size: 14px;">
            Код действителен в течение 15 минут.
        </p>
        
        <p class="message" style="text-align: center; color: #999; font-size: 12px; margin-top: 30px;">
            Если вы не запрашивали этот код, просто проигнорируйте это письмо.
        </p>
        
        <div class="footer">
            <p>© 2025 LearnHub LMS. Все права защищены.</p>
        </div>
    </div>
</body>
</html>
"""

    def render_password_reset_template(self, code: str, user_name: str) -> str:
        """
        Render HTML template for password reset code.
        
        Args:
            code: 6-digit verification code
            user_name: User's name
            
        Returns:
            HTML email body
        """
        return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Восстановление пароля</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 32px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .code-container {{
            background: rgba(102, 126, 234, 0.1);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(102, 126, 234, 0.3);
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            margin: 30px 0;
        }}
        .code {{
            font-size: 48px;
            font-weight: bold;
            letter-spacing: 8px;
            color: #667eea;
            font-family: 'Courier New', monospace;
        }}
        .message {{
            color: #333;
            line-height: 1.6;
            margin: 20px 0;
        }}
        .warning {{
            background: rgba(255, 193, 7, 0.1);
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">LearnHub LMS</div>
        </div>
        
        <h1 style="color: #333; text-align: center;">Восстановление пароля</h1>
        
        <p class="message">
            Здравствуйте, <strong>{user_name}</strong>!
        </p>
        
        <p class="message">
            Вы запросили восстановление пароля. Используйте следующий код для подтверждения:
        </p>
        
        <div class="code-container">
            <div class="code">{code}</div>
        </div>
        
        <div class="warning">
            <p style="margin: 0; color: #856404;">
                <strong>⚠️ Важно:</strong> Если вы не запрашивали восстановление пароля, 
                немедленно свяжитесь с поддержкой.
            </p>
        </div>
        
        <p class="message" style="text-align: center; color: #666; font-size: 14px;">
            Код действителен в течение 15 минут.
        </p>
        
        <div class="footer">
            <p>© 2025 LearnHub LMS. Все права защищены.</p>
        </div>
    </div>
</body>
</html>
"""

    def render_welcome_template(self, user_name: str) -> str:
        """
        Render HTML template for welcome email.
        
        Args:
            user_name: User's name
            
        Returns:
            HTML email body
        """
        return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Добро пожаловать!</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 32px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .message {{
            color: #333;
            line-height: 1.6;
            margin: 20px 0;
        }}
        .button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            margin: 20px 0;
            text-align: center;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">LearnHub LMS</div>
        </div>
        
        <h1 style="color: #333; text-align: center;">Добро пожаловать в LearnHub!</h1>
        
        <p class="message">
            Здравствуйте, <strong>{user_name}</strong>!
        </p>
        
        <p class="message">
            Спасибо за регистрацию в LearnHub LMS — платформе для обучения системных аналитиков.
        </p>
        
        <p class="message">
            Теперь вы можете:
        </p>
        
        <ul style="color: #333; line-height: 2;">
            <li>Проходить тесты и получать персональные рекомендации</li>
            <li>Отслеживать свой прогресс обучения</li>
            <li>Изучать курсы и практические задания</li>
        </ul>
        
        <div style="text-align: center;">
            <a href="#" class="button">Начать обучение</a>
        </div>
        
        <div class="footer">
            <p>© 2025 LearnHub LMS. Все права защищены.</p>
        </div>
    </div>
</body>
</html>
"""


# Global email service instance
email_service = EmailService()

