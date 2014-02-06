#include <math.h>
#define STEP_DIFF 1.08

// 计算攻击力
// 参数： 等级， 阶数， 攻击成长
float hero_attack(int level, int step, float growing);

// 计算防御力
// 参数： 等级， 阶数， 防御成长
float hero_defense(int level, int step, float growing);

// 计算生命值
// 参数： 等级， 阶数， 生命成长
float hero_hp(int level, int step, float growing);

