import csv

from preset._base import data_path

def load_data():
    with open(data_path('level_totalexp.csv'), 'r') as f:
        reader = csv.reader(f)
        data = {int(level): int(exp) for level, exp in reader}

    return data


class _Level_TotalExp(object):
    def __init__(self):
        self.level_totalexp_dict = load_data()
        self.level_totalexp_tuple = self.level_totalexp_dict.items()
        self.level_totalexp_tuple.sort(key=lambda item: item[0])
        
        self.max_level = self.level_totalexp_tuple[-1][0]
        self.max_level_exp = self.level_totalexp_tuple[-2][1]
        

    def __getitem__(self, exp):
        # return (level, current_exp, next_level_exp)
        if exp < self.level_totalexp_dict[1]:
            return (1, exp, self.level_totalexp_dict[1])

        if exp >= self.max_level_exp:
            return (self.max_level,
                    exp - self.max_level_exp,
                    0
                    )

        for level, totalexp in self.level_totalexp_tuple:
            if totalexp > exp:
                return (level,
                        exp - self.level_totalexp_dict[level-1],
                        self.level_totalexp_dict[level+1] - totalexp
                        )
    

LEVEL_TOTALEXP = _Level_TotalExp()


