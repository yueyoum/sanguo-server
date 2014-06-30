from core.drives import redis_client
redis_client.ping()

import startup
import callbacks.signals
