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
            ti, i, j, k = map(int, vals[0:4])
            vals = map(float, vals[4:])
            a[i - 1, j - 1, k - 1] = sum(vals)
        return x, y, z, a


def c_to_i(xmin, xmax, N, x):
    """
    xmin, xmax -- mesh baoundary, N -- number of mesh elements (not boundaries)
    x -- center's coordinate, which index to compute.

    returns i -- index of the mesh element, where x is located, i from 0 to N-1

        x = xmin + dx*i + dx/2, where dx = (xmax - xmin )/N

    exact expression for i:

        i = (x - dx/2 - xmin) / dx
        i = (x - xmin)/dx - 0.5

    Python truncates the deximal part when converting from float to integer.
    Thus, assuming that x always above xmin:

        0 < (x - xmin)/dx < 1.0   for x in the 1-st mesh element
        i < (x - xmin)/dx < i + 1 for x in the i-th mesh element

    thus, converting (x - xmin)/dx to integer gives the zero-based mesh index.
    """
    dx = (xmax - xmin)/N
    ii = (x - xmin) / dx
    return int(ii)


def readdgs_old(fname):
    with open(fname) as f:
        # read header
        tokens = f.readline().split()
        xmin, xmax = map(float, tokens[0:2])
        ymin, ymax = map(float, tokens[3:5])
        zmin, zmax = map(float, tokens[6:8])
        xn, yn, zn, n = map(int, tokens[2::3])

        dx = (xmax - xmin) / xn
        dy = (ymax - ymin) / yn
        dz = (zmax - zmin) / zn

        x = map(lambda i: xmin + i*dx + dx/2., range(xn+1))
        y = map(lambda i: ymin + i*dy + dy/2., range(yn+1))
        z = map(lambda i: zmin + i*dz + dz/2., range(zn+1))

        # read data
        a = zeros((xn, yn, zn))
        for k in tqdm(range(n)):
            vals = f.readline().split()
            xi, yi, zi = map(float, vals[0:3])
            i = c_to_i(xmin, xmax, xn, xi)
            j = c_to_i(ymin, ymax, yn, yi)
            k = c_to_i(zmin, zmax, zn, zi)

            # check coordinate to index conversion
            assert abs(xi - x[i]) < 0.01
            assert abs(yi - y[j]) < 0.01
            assert abs(zi - z[k]) < 0.01
            vals = map(float, vals[3:])
            a[i, j, k] = sum(vals)

        return x, y, z, a

if __name__ == '__main__':
    from sys import argv
    x, y, z, a = readdgs(argv[1])
    print len(x), len(y), len(z), a.shape
