#include <math.h>
#include "external_calculate.h"

const float Hero::step_diff = 1.08;
const int Hero::modulus_attack = 20;
const int Hero::modulus_defense = 15;
const int Hero::modulus_hp = 45;

const int Hero::hero_to_soul_table[] = {120, 60, 30};
const int Hero::step_up_gold_table[] = {10000, 5000, 1000};


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

int Hero::step_up_using_soul_amount(int quality)
{
    if(quality <1 or quality >3) return 0;
    return hero_to_soul_table[quality-1];
}

int Hero::step_up_using_gold(int quality)
{
    if(quality <1 or quality >3) return 0;
    return step_up_gold_table[quality-1];
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


