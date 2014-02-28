#include "hero.h"

float hero_calculate(int modulus, int level, int step, int quality, float growing)
{
    float step_adjust = pow(STEP_DIFF, step-1);
    float value = modulus * step * (4-quality) * 1.2 + level * growing * step_adjust;
    return value;
}


float hero_attack(int level, int step, int quality, float growing)
{
    return hero_calculate(20, level, step, quality, growing);
}

float hero_defense(int level, int step, int quality, float growing)
{
    return hero_calculate(15, level, step, quality, growing);
}

float hero_hp(int level, int step, int quality, float growing)
{
    return hero_calculate(45, level, step, quality, growing);
}


