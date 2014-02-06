
hero.o: hero.h hero.c
	gcc -c hero.c -Wall

equipment.o: equipment.h equipment.c
	gcc -c equipment.c -Wall

sanguo.so: hero.o equipment.o
	gcc hero.o equipment.o -o sanguo.so -fPIC -shared -lm


.PHONY: clean
clean:
	-rm -f hero.o equipment.o sanguo.so

