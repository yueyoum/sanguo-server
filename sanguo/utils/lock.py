# -*- coding: utf-8 -*-
"""
Author:         Wang Chao <yueyoum@gmail.com>
Filename:       lock
Date Created:   2016-01-26 15-29
Description:

"""

import time

from contextlib import contextmanager
from core.drives import redis_client
from core.server import server


class LockTimeOut(Exception):
    pass


class Lock(object):
    INTERVAL = 0.1

    def __init__(self, key):
        self.key = key

    @contextmanager
    def lock(self, timeout=5):
        key = "{0}:{1}".format(self.key, server.id)

        t = 0
        while True:
            if t > timeout:
                raise LockTimeOut()

            # 程序期望获取到锁的等待时间是timeout
            # 那么这个锁的过期时间就简单设置成 timeout+1
            # 过期时间可以理解为程序期望获得锁以后，直到释放锁的运行时间
            # 不太可能会有这样的需求： 我期望等待10秒，但获取到锁后，只运行1秒
            # 或者 我期望等待1秒，但是获取到锁以后 要运行10秒
            # 一般都是 等待时间，于期望运行时间差不多
            result = redis_client.set(key, 1, ex=timeout+1, nx=True)
            if result:
                # got the lock
                break

            time.sleep(self.INTERVAL)
            t += self.INTERVAL

        try:
            yield
        finally:
            redis_client.delete(key)
