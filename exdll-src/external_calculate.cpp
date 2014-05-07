#include <math.h>
#include "external_calculate.h"



int Hero::_calculate(int m, int level, int step, int quality, float growing)
{
    float step_adjust = pow(step_diff, step);
    float value = m * (step+1) * (4-quality) * 1.2 + level * growing * step_adjust;
    return int(value);
}

int Hero::attack(int level, int step, int quality, float growing)
{
    return _calculate(modulus_attack, level, step, quality, growing);
}

int Hero::defense(int level, int step, int quality, float growing)
{
    return _calculate(modulus_defense, level, step, quality, growing);
}

int Hero::hp(int level, int step, int quality, float growing)
{
    return _calculate(modulus_hp, level, step, quality, growing);
}



int Equipment::attack(int base, int level, int growing)
{
    return base + level * growing;
}

int Equipment::defense(int base, int level, int growing)
{
    return base + level * growing;
}

int Equipment::hp(int base, int level, int growing)
{
    return base + level * growing;
}


