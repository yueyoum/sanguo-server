from definition import LEVEL_TOTALEXP

def test_level_totalexp():
    level, current_exp, max_exp = LEVEL_TOTALEXP[1]
    assert level == 1
    assert current_exp == 1
    assert max_exp == LEVEL_TOTALEXP.min_level_exp

    total_exp = LEVEL_TOTALEXP.min_level_exp
    level, current_exp, max_exp = LEVEL_TOTALEXP[total_exp]
    assert level == 2
    assert current_exp == 0
    assert max_exp == LEVEL_TOTALEXP.level_totalexp_dict[3] - total_exp

    total_exp = LEVEL_TOTALEXP.max_level_exp
    level, current_exp, max_exp = LEVEL_TOTALEXP[total_exp]
    assert level == LEVEL_TOTALEXP.max_level
    assert current_exp == LEVEL_TOTALEXP.max_level_exp - LEVEL_TOTALEXP.level_totalexp_dict[level-1]
    assert max_exp == 0


