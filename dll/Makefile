
hero.o: hero.h hero.c
	gcc -c hero.c -Wall -fPIC

equipment.o: equipment.h equipment.c
	gcc -c equipment.c -Wall -fPIC

sanguo.so: hero.o equipment.o
	gcc hero.o equipment.o -o sanguo.so -fPIC -shared -lm


.PHONY: clean
clean:
	-rm -f hero.o equipment.o sanguo.so

