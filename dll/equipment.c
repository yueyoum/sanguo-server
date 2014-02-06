#include "equipment.h"

int equip_calculate(int value, int level, int growing)
{
    return value + level * growing;
}

int equip_attack(int base_value, int level, int growing)
{
    return equip_calculate(base_value, level, growing);
}

int equip_defense(int base_value, int level, int growing)
{
    return equip_calculate(base_value, level, growing);
}

int equip_hp(int base_value, int level, int growing)
{
    return equip_calculate(base_value, level, growing);
}

