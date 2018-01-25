# Operations with dgs files
from numpy import zeros
from tqdm import tqdm


def readdgs(fname):
    with open(fname) as f:
        # read header
        ni, nj, nk = map(int, f.readline().split())
        x = map(float, f.readline().split())
        y = map(float, f.readline().split())
        z = map(float, f.readline().split())
        ne = int(f.readline())
        # read data
        a = zeros((ni - 1, nj - 1, nk - 1))
        for k in tqdm(range(ne)):
            vals = f.readline().split()
            ti, ii, ji, ki = map(int, vals[0:4])
            vals = map(float, vals[4:])
            a[ii - 1, ji - 1, ki - 1] = sum(vals)

        return x, y, z, a

if __name__ == '__main__':
    from sys import argv
    x, y, z, a = readdgs(argv[1])
    print len(x), len(y), len(z), a.shape
