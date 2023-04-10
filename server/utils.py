import numpy as np
import random

def gen_q_old():
    while True:
        a = np.random.randint(0, 100)
        b = np.random.randint(0, 100)
        f = random.choice(['+', '-', 'X'])
        if f == '+' and a + b < 100:
            return f'{a}+{b}', a+b
        elif f == '-' and a - b >= 0:
            return f'{a}-{b}', a-b
        elif f == 'X' and a * b < 100:
            return f'{a}X{b}', a*b

def gen_q():
    while True:
        f = random.choice(['+', '-', 'X'])
        if f == '+':
            a = np.random.randint(0, 100)
            b = np.random.randint(0, 100)
            if a + b < 100:
                return f'{a}+{b}', a+b
        elif f == '-':
            a = np.random.randint(0, 100)
            b = np.random.randint(0, 100)
            if a - b >= 0:
                return f'{a}-{b}', a-b
        elif f == 'X':
            a = np.random.randint(0, 15)
            b = np.random.randint(0, 15)
            if a * b < 100:
                return f'{a}X{b}', a*b