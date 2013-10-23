
def _check_valid():
    from core import redis_client
    redis_client.ping()


_check_valid()
del _check_valid

