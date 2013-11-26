import redisco

from django.conf import settings

from core.drives import redis_client
redis_client.ping()

redisco.connection_setup(
    host = settings.REDIS_HOST,
    port = settings.REDIS_PORT,
    db = settings.REDIS_DB
)

