from pathlib import Path 
from fastapi_mail import FastMail , MessageSchema, ConnectionConfig , MessageType
from jinja2 import Environment, FileSystemLoader

from app.core.config import get_settings

settings = get_settings()

conf = ConnectionConfig(
    MAIL_USERNAME = settings.MAIL_USERNAME,
    MAIL_PASSWORD = settings.MAIL_PASSWORD,
    MAIL_FROM = settings.MAIL_FROM,
    MAIL_FROM_NAME = settings.MAIL_FROM_NAME,
    MAIL_SERVER = settings.MAIL_SERVER,
    MAIL_PORT = settings.MAIL_PORT,
    MAIL_STARTTLS = settings.MAIL_STARTTLS,
    MAIL_SSL_TLS = settings.MAIL_SSL_TLS,
    USE_CREDENTIALS = True,
)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

async def send_order_confirmation_email(
    to_email: str , full_name: str , order_id: str , items: list[dict] , total_amount: str
) -> None:
    template = jinja_env.get_template("order_confirmation.html")
    html_content = template.render(
        full_name=full_name , order_id=order_id , items=items , total_amount=total_amount
    )
    
    message = MessageSchema(
        subject=f"Order Confirmation - #{order_id}",
        recipients=[to_email],
        body=html_content,
        subtype=MessageType.html,
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
