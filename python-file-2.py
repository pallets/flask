def i4():
        home = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f':6}
        home_triple = {x:y for (x,y) in home.items() if y>2 if y%2 == 0 if y%3 == 0}
        print(home_triple)
def _main():
        i4();
        print("Hello world")