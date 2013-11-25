from preset import LEVEL_TOTALEXP

def test_level_totalexp():
    level, current_exp, max_exp = LEVEL_TOTALEXP[1]
    assert level == 1
    assert current_exp == 1
    assert max_exp == LEVEL_TOTALEXP.level_totalexp_dict[1]

    total_exp = LEVEL_TOTALEXP.level_totalexp_dict[1]
    level, current_exp, max_exp = LEVEL_TOTALEXP[total_exp]
    assert level == 2
    assert current_exp == 0
    assert max_exp == LEVEL_TOTALEXP.level_totalexp_dict[3] - LEVEL_TOTALEXP.level_totalexp_dict[2]

    total_exp = LEVEL_TOTALEXP.max_level_exp
    level, current_exp, max_exp = LEVEL_TOTALEXP[total_exp]
    assert level == LEVEL_TOTALEXP.max_level
    assert current_exp == total_exp - LEVEL_TOTALEXP.max_level_exp
    assert max_exp == 0


