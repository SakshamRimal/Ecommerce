from arq.connections import RedisSettings
from app.core.config import get_settings
from app.jobs.tasks import index_product_task , delete_product_from_index_task , send_order_confirmation_task

settings = get_settings()

class WorkerSettings:
    functions = [index_product_task , delete_product_from_index_task , 
                 send_order_confirmation_task]
    redis_settings = RedisSettings.from_dsn(settings.arq_redis_url)
    max_jobs = 10
    job_timeout = 60  # seconds
    

