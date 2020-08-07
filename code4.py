def main():
    var l = {'a','b','c','d','e'}
    for i in range(len(l)):
        x = l[i]
        y = l[i+1]
    try:
        x = next(i for i, n in enumerate(l) if n > 0)
    except StopIteration:
        print('No positive numbers')
    else:
        print('The index of the first positive number is', x)