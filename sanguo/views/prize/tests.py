# from django.test import TransactionTestCase
# import protomsg
#
# from core.character import char_initialize
# from utils import crypto
# from utils import app_test_helper as tests
#
#
# class PrizeTest(TransactionTestCase):
#     def setUp(self):
#         char = char_initialize(1, 1, 'a')
#         self.char_id = char.id
#         self.session = crypto.encrypt('1:1:{0}'.format(char.id))
#
#     def tearDown(self):
#         tests._teardown()
#
#
#     def _prize_get(self, pid):
#         req = protomsg.PrizeRequest()
#         req.session = self.session
#         req.prize_id = pid
#
#         data = tests.pack_data(req)
#         res = tests.make_request('/prize/', data)
#         msgs = tests.unpack_data(res)
#
#         return msgs
#
# 
#     def test_error_prize(self):
#         msgs = self._prize_get(1)
#
#
#     def test_normal_prize(self):
#         from core.mongoscheme import MongoHang
#
#         h = MongoHang(
#             id=self.char_id,
#             stage_id=1,
#             start=100,
#             finished=True,
#             actual_seconds=800,
#             plunder_gold=0,
#         )
#
#         h.save()
#
#         msgs = self._prize_get(1)
#
#
