from level_totalexp import level_totalexp_dict

class _LevelTotalExp(object):
    def __init__(self):
        self.level_totalexp_dict = level_totalexp_dict
        self.level_totalexp_tuple = level_totalexp_dict.items()
        self.level_totalexp_tuple.sort(key=lambda item: item[0])
        self.max_level = self.level_totalexp_tuple[-1][0]

        self.max_level_exp = self.level_totalexp_tuple[-1][1]
        self.min_level_exp = self.level_totalexp_tuple[0][1]

    def __getitem__(self, exp):
        if exp < self.min_level_exp:
            return 1, exp, self.min_level_exp

        if exp >= self.max_level_exp:
            return (self.max_level,
                    self.max_level_exp - self.level_totalexp_tuple[-2][1],
                    0
                    )

        for level, totalexp in self.level_totalexp_tuple:
            if totalexp >= exp:
                return (level,
                        exp - totalexp,
                        self.level_totalexp_dict[level+1] - totalexp
                        )

LEVEL_TOTALEXP = _LevelTotalExp()


