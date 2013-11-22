"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, TransactionTestCase

import protomsg
from protomsg import (
        RESPONSE_NOTIFY_TYPE,
        CommandResponse,
        CreateCharacterRequest,
        CreateCharacterResponse,
        CharacterNotify,

        GetHeroRequest,
        GetHeroResponse,
        MergeHeroRequest,
        MergeHeroResponse,

        SetFormationRequest,
        SetFormationResponse,
        )

from utils import app_test_helper
from models import Character, CharHero
from utils import crypto
from core import GLOBAL


def teardown():
    from core.drives import redis_client, mongodb_client, mongodb_client_db
    redis_client.flushdb()
    mongodb_client.drop_database(mongodb_client_db)


class CreateCharacterTest(TransactionTestCase):
    def setUp(self):
        Character.objects.create(
                account_id = 1,
                server_id = 1,
                name = "abcd"
                )

    def _create(self, account_id, server_id, name, ret):
        session = crypto.encrypt("{0}:{1}".format(account_id, server_id))
        req = CreateCharacterRequest()
        req.session = session
        req.name = name

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/char/create/', data)

        msgs = app_test_helper.unpack_data(res)
        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["CommandResponse"]:
                data = CommandResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)

    def test_normal_create(self):
        self._create(1, 2, "123", 0)

    def test_already_created(self):
        self._create(1, 1, "123", 200)

    def test_name_has_been_taken(self):
        self._create(2, 1, "abcd", 201)

    def test_invalid_name_length(self):
        self._create(2, 2, "12345678", 202)


class GetHeroTest(TransactionTestCase):
    fixtures = ['get_hero.json']

    def setUp(self):
        Character.objects.create(
                account_id = 1,
                server_id = 1,
                name = "abcd"
                )

    def _get_hero(self, ten, ret=0):
        session = crypto.encrypt('1:1:1')
        req = GetHeroRequest()
        req.session = session
        req.mode = 1
        req.ten = ten

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/hero/get/', data)
        msgs = app_test_helper.unpack_data(res)

        possible_ids = [
                RESPONSE_NOTIFY_TYPE["GetHeroResponse"],
                RESPONSE_NOTIFY_TYPE["AddHeroNotify"],
                ]
        for id_of_msg, len_of_msg, msg in msgs:
            self.assertTrue(id_of_msg in possible_ids)
            if id_of_msg == RESPONSE_NOTIFY_TYPE["GetHeroResponse"]:
                data = GetHeroResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)

    def test_get_one_hero(self):
        self._get_hero(False)
        self.assertEqual(
                CharHero.objects.filter(char_id=1).count(),
                1
                )

    def test_get_ten_hero(self):
        self._get_hero(True)
        self.assertEqual(
                CharHero.objects.filter(char_id=1).count(),
                10
                )


class MergeHeroTest(TransactionTestCase):
    def setUp(self):
        Character.objects.create(
                account_id = 1,
                server_id = 1,
                name = "abcd"
                )

    def _merge_hero(self, using_hero_ids, ret=0):
        session = crypto.encrypt('1:1:1')
        req = MergeHeroRequest()
        req.session = session
        req.using_hero_ids.extend(using_hero_ids)

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/hero/merge/', data)
        msgs = app_test_helper.unpack_data(res)

        possible_ids = [
                RESPONSE_NOTIFY_TYPE["MergeHeroResponse"],
                RESPONSE_NOTIFY_TYPE["RemoveHeroNotify"],
                RESPONSE_NOTIFY_TYPE["AddHeroNotify"],
                RESPONSE_NOTIFY_TYPE["HeroNotify"],
                ]

        for id_of_msg, len_of_msg, msg in msgs:
            self.assertTrue(id_of_msg in possible_ids)
            if id_of_msg == RESPONSE_NOTIFY_TYPE["MergeHeroResponse"]:
                data = MergeHeroResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)

    def test_normal_two_merge(self):
        one_heros = GLOBAL.HEROS.get_hero_ids_by_quality(1)[:2]
        char_heros_list = [
                CharHero(char_id=1, hero_id=h) for h in one_heros
                ]

        char_heros = CharHero.multi_create(char_heros_list)
        using_hero_ids = [c.id for c in char_heros]

        self._merge_hero(using_hero_ids)
        self.assertEqual(
                CharHero.objects.filter(char_id=1).count(),
                1
                )

    def test_normal_eight_merge(self):
        two_heros = GLOBAL.HEROS.get_hero_ids_by_quality(2)[:8]
        char_heros_list = [
                CharHero(char_id=1, hero_id=h) for h in two_heros
                ]

        char_heros = CharHero.multi_create(char_heros_list)
        using_hero_ids = [c.id for c in char_heros]

        self._merge_hero(using_hero_ids)
        self.assertEqual(
                CharHero.objects.filter(char_id=1).count(),
                1
                )

    def test_error_eight_merge(self):
        two_heros = GLOBAL.HEROS.get_hero_ids_by_quality(1)[:8]
        char_heros_list = [
                CharHero(char_id=1, hero_id=h) for h in two_heros
                ]

        char_heros = CharHero.multi_create(char_heros_list)
        using_hero_ids = [c.id for c in char_heros]

        self._merge_hero(using_hero_ids, 302)


    def test_merge_with_non_exits(self):
        self._merge_hero([100, 101], 300)

    def test_merge_with_three_one(self):
        one_heros = GLOBAL.HEROS.get_hero_ids_by_quality(1)[:3]
        char_heros_list = [
                CharHero(char_id=1, hero_id=h) for h in one_heros
                ]

        char_heros = CharHero.multi_create(char_heros_list)
        using_hero_ids = [c.id for c in char_heros]
        self._merge_hero(using_hero_ids, 302)

    def test_merge_with_different_quality(self):
        one_heros = GLOBAL.HEROS.get_hero_ids_by_quality(1)[:3]
        two_heros = GLOBAL.HEROS.get_hero_ids_by_quality(2)[:5]
        one_heros = list(one_heros)
        one_heros.extend(two_heros)

        char_heros_list = [
                CharHero(char_id=1, hero_id=h) for h in one_heros
                ]

        char_heros = CharHero.multi_create(char_heros_list)

        using_hero_ids = [c.id for c in char_heros]

        self._merge_hero(using_hero_ids, 301)


class FormationTest(TransactionTestCase):
    def setUp(self):
        Character.objects.create(account_id=1, server_id=1)
        self.socket_ids = [0, 0, 0, 0, 0, 0, 0, 0, 0]

    def _set_formation(self, ret=0):
        session = crypto.encrypt('1:1:1')
        req = SetFormationRequest()
        req.session = session
        req.socket_ids.extend(self.socket_ids)

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/formation/set/', data)
        msgs = app_test_helper.unpack_data(res)
        print msgs

        possible_ids = [
                RESPONSE_NOTIFY_TYPE["SetFormationResponse"],
                RESPONSE_NOTIFY_TYPE["FormationNotify"],
                ]

        for id_of_msg, len_of_msg, msg in msgs:
            self.assertTrue(id_of_msg in possible_ids)
            if id_of_msg == RESPONSE_NOTIFY_TYPE["SetFormationResponse"]:
                data = MergeHeroResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)

            elif id_of_msg == RESPONSE_NOTIFY_TYPE["FormationNotify"]:
                data = getattr(protomsg, "FormationNotify")()
                data.ParseFromString(msg)
                self.assertEqual(len(data.socket_ids), 9)

    def test_set_formation(self):
        self._set_formation()



