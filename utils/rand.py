import random
import string


def randint_n(n, m=9):
    # m - max first digit
    # If the length is 1, starts from 2 to avoid
    # number repetition on evaluation e.g. 1*8=8
    # creating false positives
    if n == 1:
        range_start = 2
    else:
        range_start = 10**(n-1)
    range_end = (m+1)*(10**(n-1))-1
    return random.randint(range_start, range_end)


letters = string.ascii_letters


def randstr_n(n, chars=letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(n))


# Generate static random integers
# to help filling actions['render']
randints = [randint_n(2) for _ in range(3)]

# Generate static random integers
# to help filling actions['render']
randstrings = [randstr_n(2) for _ in range(3)]
