# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/20/14'

import traceback

import uwsgidecorators

from cron.log import Logger

import traceback
import json
from core.mongoscheme import MongoPurchaseRecord
from core.purchase import BasePurchaseAction, YuekaLockTimeOut
from core.attachment import make_standard_drop_from_template
from core.mail import Mail

from preset.settings import MAIL_YUEKA_CONTENT_TEMPLATE, MAIL_YUEKA_TITLE

def send_yueka_reward(char_id, sycee, remained_days):
    standard_drop = make_standard_drop_from_template()
    standard_drop['sycee'] = sycee

    content = MAIL_YUEKA_CONTENT_TEMPLATE.format(sycee, remained_days)

    Mail(char_id).add(MAIL_YUEKA_TITLE, content, attachment=json.dumps(standard_drop), only_one=True)

@uwsgidecorators.cron(0, 0, -1, -1, -1, target="mule")
def set_yueka(signum):
    logger = Logger('set_yueka.log')
    logger.write("Start")

    records = MongoPurchaseRecord.objects.filter(yueka_remained_days__gt=0)

    for record in records:
        if record.yueka_remained_days > 0:
            # 发送奖励，并且days-1
            send_yueka_reward(record.id, record.yueka_sycee, record.yueka_remained_days-1)

            pa = BasePurchaseAction(record.id)
            try:
                pa.set_yueka_remained_days(-1)
            except YuekaLockTimeOut:
                logger.error(traceback.format_exc())

    logger.write("Done")
    logger.close()
