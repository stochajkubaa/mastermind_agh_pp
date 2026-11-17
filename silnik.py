import random

def generuj_kod_easy():
    return [random.randint(0, 3) for _ in range(4)]

def generuj_kod_hard():
    return [random.randint(0, 9) for _ in range(4)]

