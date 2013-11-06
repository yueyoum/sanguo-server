TARGET_RULE = {
        0: [0, 1, 2],
        1: [1, 0, 2],
        2: [2, 1, 0],
        }


class BattleField(object):
    def __init__(self, team_one, team_two, msg):
        self.team_one = team_one
        self.team_two = team_two

        for index, h in enumerate(self.team_one):
            if h is not None:
                h._index = index
                h._team = self.team_one
                h.ground_msg = msg

        for index, h in enumerate(self.team_two):
            if h is not None:
                h._index = index
                h._team = self.team_two
                h.ground_msg = msg

        self.current_pos = 0

    def change_current_pos(self):
        self.current_pos += 1
        if self.current_pos >= 3:
            self.current_pos = 0

    def action(self):
        hero_pairs = self.find_hero_pairs()
        _p = []
        for a, b in hero_pairs:
            _p.append((a.id, b.id))
        print "hero_pairs =", _p
        for a, b in hero_pairs:
            print "BattleField, ", a.id, b.id
            print a.id, "die =", a.die
            a.action(b)
            print b.id, "die =", b.die
            # b.action(a)
            # print a.id, "die =", a.die
            # print


    def find_hero_pairs(self):
        while True:
            hero = self.team_one[self.current_pos]
            if hero is None or hero.die:
                opposite = self.team_two[self.current_pos]
                if opposite is None or opposite.die:
                    self.change_current_pos()
                    continue

                hero = self.choose_target(self.team_one, self.current_pos)
                self.change_current_pos()
                return ((opposite, hero),)


            target = self.choose_target(self.team_two, self.current_pos)
            target_target = self.choose_target(self.team_one, target._index)
            self.change_current_pos()
            return ((hero, target), (target, target_target),)

                

    def choose_target(self, base, index):
        for pos in TARGET_RULE[index]:
            h = base[pos]
            if h is None or h.die:
                continue
            
            return h

        raise Exception("choose_target error")


