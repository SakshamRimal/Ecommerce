from pathlib import Path 
from fastapi_mail import FastMail , MessageSchema, ConnectionConfig , MessageType
from jinja2 import Environment, FileSystemLoader

from app.core.config import get_settings

settings = get_settings()

conf = ConnectionConfig(
    MAIL_USERNAME = settings.mail_username,
    MAIL_PASSWORD = settings.mail_password,
    MAIL_FROM = settings.mail_from,
    MAIL_FROM_NAME = settings.mail_from_name,
    MAIL_SERVER = settings.mail_server,
    MAIL_PORT = settings.mail_port,
    MAIL_STARTTLS = settings.mail_starttls,
    MAIL_SSL_TLS = settings.mail_ssl_tls,
    USE_CREDENTIALS = True,
)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

async def send_order_confirmation_email(
    to_email: str , full_name: str , order_id: str , items: list[dict] , total_amount: str
) -> None:
    template = jinja_env.get_template("order_confirmation.html")
    html_content = template.render(
        full_name=full_name, order_id=order_id, order_items=items, total_amount=total_amount
    )
    
    message = MessageSchema(
        subject=f"Order Confirmation - #{order_id}",
        recipients=[to_email],
        body=html_content,
        subtype=MessageType.html,
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
