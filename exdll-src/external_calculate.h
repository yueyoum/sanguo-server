class Hero
{
    private:
        static const float step_diff = 1.08;
        static const int modulus_attack = 20;
        static const int modulus_defense = 15;
        static const int modulus_hp = 45;

        static int _calculate(int, int, int,int, float);

    public:
        static int attack(int, int, int, float);
        static int defense(int, int, int, float);
        static int hp(int, int, int, float);
};

class Equipment
{
    public:
        static int attack(int, int, int);
        static int defense(int, int, int);
        static int hp(int, int, int);

};


