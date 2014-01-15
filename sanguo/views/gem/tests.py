from django.test import TransactionTestCase
import protomsg
from protomsg import RESPONSE_NOTIFY_TYPE

from core.character import char_initialize
from utils import app_test_helper as tests
from utils import crypto
from apps.character.models import Character

from core.item import Item

class GemTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        gems = (
            (49, 4),
            (48, 3),

            (47, 4),
        )
        item = Item(char.id)
        item.gem_add(gems)
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
        self.char_id = char.id

    def tearDown(self):
        tests._teardown()


    def _merge(self, _id, _amount, using_sycee, ret=0):
        req = protomsg.MergeGemRequest()
        req.session = self.session
        req.id = _id
        req.amount = _amount
        req.using_sycee = using_sycee

        data = tests.pack_data(req)
        res = tests.make_request('/gem/merge/', data)
        msgs = tests.unpack_data(res)

        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["MergeGemResponse"]:
                data = protomsg.MergeGemResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)


    def test_normal_merge_with_not_enough_gold(self):
        self._merge(50, 1, False, 10)

    def test_normal_merge(self):
        c = Character.objects.get(id=self.char_id)
        c.gold = 9999
        c.save()
        self._merge(50, 1, False)

    def test_error_merge(self):
        self._merge(49, 1, False, ret=600)

    def test_error_using_sycee(self):
        self._merge(49, 2, True, 11)

    def test_normal_using_sycee(self):
        c = Character.objects.get(id=self.char_id)
        c.sycee = 9999 * 10000
        c.save()
        self._merge(49, 2, True)



