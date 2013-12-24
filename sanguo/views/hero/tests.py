
from django.test import TransactionTestCase
import protomsg
from protomsg import RESPONSE_NOTIFY_TYPE
from utils import app_test_helper

from core import GLOBAL
from utils import crypto
from core.hero import save_hero
from core.mongoscheme import MongoChar, MongoHero
from apps.character.models import Character
from core.character import Char, char_initialize


DRAW_HERO = GLOBAL.SETTINGS.DRAW_HERO


class GetHeroTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.char_id = char.id
        
    def tearDown(self):
        app_test_helper._teardown()

    def _get_hero(self, ten, ret=0):
        session = crypto.encrypt('1:1:{0}'.format(self.char_id))
        req = protomsg.GetHeroRequest()
        req.session = session
        req.mode = 1
        req.ten = ten

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/hero/get/', data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["GetHeroResponse"]:
                data = protomsg.GetHeroResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)
    
    def test_not_enough_sycee(self):
        self._get_hero(False, 11)
        

    def test_get_one_hero(self):
        c = Character.objects.get(id=self.char_id)
        c.sycee = DRAW_HERO[1]['sycee']
        c.save()
        
        cache_char = Char(self.char_id).cacheobj
        self.assertEqual(cache_char.sycee, c.sycee)
        
        self._get_hero(False)
        count = len( MongoHero.objects(char=1) )
        self.assertEqual(count, 1 + 3)
        
        cache_char = Char(self.char_id).cacheobj
        self.assertEqual(cache_char.sycee, 0)
        
        app_test_helper._mongo_teardown_func()

    def test_get_ten_hero(self):
        c = Character.objects.get(id=self.char_id)
        c.sycee = DRAW_HERO[1]['sycee'] * 10
        c.save()
        
        cache_char = Char(self.char_id).cacheobj
        self.assertEqual(cache_char.sycee, c.sycee)
        
        self._get_hero(True)
        count = len( MongoHero.objects(char=1) )
        self.assertEqual(count ,10 + 3)
        
        cache_char = Char(self.char_id).cacheobj
        self.assertEqual(cache_char.sycee, 0)
        
        app_test_helper._mongo_teardown_func()


class MergeHeroTest(TransactionTestCase):
    def setUp(self):
        char_initialize(1, 1, 'a')
        
    def tearDown(self):
        app_test_helper._teardown()

    def _merge_hero(self, using_hero_ids, ret=0):
        session = crypto.encrypt('1:1:1')
        req = protomsg.MergeHeroRequest()
        req.session = session
        req.using_hero_ids.extend(using_hero_ids)

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/hero/merge/', data)
        msgs = app_test_helper.unpack_data(res)


        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["MergeHeroResponse"]:
                data = protomsg.MergeHeroResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)

    
    def test_normal_two_merge(self):
        one_heros = GLOBAL.HEROS.get_hero_ids_by_quality(1)[:2]
        using_hero_ids = save_hero(1, one_heros)

        self._merge_hero(using_hero_ids)
        count = len( MongoHero.objects(char=1) )
        self.assertEqual(count, 1 + 3)
        app_test_helper._mongo_teardown_func()

    def test_normal_eight_merge(self):
        two_heros = GLOBAL.HEROS.get_hero_ids_by_quality(2)[:8]
        using_hero_ids = save_hero(1, two_heros)

        self._merge_hero(using_hero_ids)
        count = len( MongoHero.objects(char=1) )
        self.assertEqual(count, 1 + 3)
        app_test_helper._mongo_teardown_func()

    def test_error_eight_merge(self):
        two_heros = GLOBAL.HEROS.get_hero_ids_by_quality(1)[:8]
        using_hero_ids = save_hero(1, two_heros)

        self._merge_hero(using_hero_ids, 302)
        app_test_helper._mongo_teardown_func()


    def test_merge_with_non_exits(self):
        self._merge_hero([100, 101], 300)
        app_test_helper._mongo_teardown_func()

    def test_merge_with_three_one(self):
        one_heros = GLOBAL.HEROS.get_hero_ids_by_quality(1)[:3]
        using_hero_ids = save_hero(1, one_heros)
        self._merge_hero(using_hero_ids, 302)
        app_test_helper._mongo_teardown_func()

    def test_merge_with_different_quality(self):
        one_heros = GLOBAL.HEROS.get_hero_ids_by_quality(1)[:3]
        two_heros = GLOBAL.HEROS.get_hero_ids_by_quality(2)[:5]
        one_heros = list(one_heros)
        one_heros.extend(two_heros)

        using_hero_ids = save_hero(1, one_heros)

        self._merge_hero(using_hero_ids, 301)
        app_test_helper._mongo_teardown_func()
