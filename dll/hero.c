#include "hero.h"

float hero_calculate(int modulus, int level, int step, float growing)
{
    float step_adjust = pow(STEP_DIFF, step-1);
    float value = modulus * step + level * growing * step_adjust;
    return value;
}


float hero_attack(int level, int step, float growing)
{
    return hero_calculate(20, level, step, growing);
}

float hero_defense(int level, int step, float growing)
{
    return hero_calculate(15, level, step, growing);
}

float hero_hp(int level, int step, float growing)
{
    return hero_calculate(45, level, step, growing);
}


