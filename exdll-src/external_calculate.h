class Hero
{
    private:
        static const float step_diff;
        static const int modulus_attack;
        static const int modulus_defense;
        static const int modulus_hp;

        static const int hero_to_soul_table[];
        static const int step_up_gold_table[];

        static int _calculate(int, int, int,int, float);

    public:
        static int attack(int, int, int, float);
        static int defense(int, int, int, float);
        static int hp(int, int, int, float);
        static int step_up_using_soul_amount(int);
        static int step_up_using_gold(int);
};


class Equipment
{
    public:
        static int attack(int, int, int);
        static int defense(int, int, int);
        static int hp(int, int, int);

};


