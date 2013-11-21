# import random
# import logging
# from core import GLOBAL
# from core.battle.battle import PVE
# from core.battle.hero import BattleHero, MonsterHero
# 
# import protomsg
# 
# 
# class _PVE(PVE):
#     def load_my_heros(self):
#         self.my_heros = []
#         original_hero_ids = GLOBAL.HEROS.keys()
#         for i in range(9):
#             # oid = random.choice(original_hero_ids)
#             # original_hero_ids.remove(oid)
#             oid = original_hero_ids[0]
#             h = BattleHero(i, oid, 100, [2])
#             h.hp = 80
#             h.attack = 100
#             h.defense = 50
#             h.crit = 0
#             h.dodge = 0
# 
#             h._hero_type = 1
#             self.my_heros.append(h)
# 
#     def load_rival_heros(self):
#         self.rival_heros = []
#         for i in range(9):
#             h = MonsterHero(i)
#             h._hero_type = 2
#             self.rival_heros.append(h)
# 
# 
# 
# def _random_skill_ids(num):
#     skill_ids = GLOBAL.SKILLS.keys()
#     res = []
#     while len(res) == num:
#         s = random.choice(skill_ids)
#         skill_ids.remove(s)
#         if s not in res:
#             res.append(s)
# 
#     return res
# 
# class TestBattle(object):
#     def setUp(self):
#         logger = logging.getLogger('battle')
#         for h in logger.handlers[:]:
#             logger.removeHandler(h)
# 
#         monster = GLOBAL.MONSTERS.values()[0]
#         new_monsters = {}
#         for i in range(9):
#             # monster['skills'] = _random_skill_ids(random.randint(1, 3))
#             monster['skills'] = [2]
#             new_monsters[i] = monster
# 
#         GLOBAL.MONSTERS = new_monsters
# 
#     def test_battle(self):
#         msg = protomsg.Battle()
#         b = _PVE(0, 0, msg)
#         b.start()
# 
# 
