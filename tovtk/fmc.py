# fine mesh content reader
from numpy import zeros
from tqdm import tqdm


def fmc_iterator(fname):
    """
    Return (yield) important blocks of the fine mesh content file.
    """
    with open(fname) as f:
        # read header
        ni, nj, nk = map(int, f.readline().split())
        x = map(float, f.readline().split())
        y = map(float, f.readline().split())
        z = map(float, f.readline().split())
        ne = int(f.readline())
        # read data
        a = zeros((ni - 1, nj - 1, nk - 1))
        yield x, y, z, ne, a
        for k in range(ne):
            yield f.readline()


def read_vol_frac(fname):
    """
    This is the file with header, exactly as dgs.

    Compute vol. frac. of materials in each fine mesh element.
    """
    fmci = fmc_iterator(fname)
    x, y, z, ne, a = fmci.next()
    for k in tqdm(range(ne)):
        vals = fmci.next().split()
        i, j, k = map(int, vals[0:3])
        vals = map(int, vals[6:])
        # cell indices
        nc = vals[0]  # number of cells detected
        nh = vals[1]  # number of samples
        # cl = vals[2::3]  # cell indices
        hl = vals[3::3]  # hits in each cell
        ml = vals[4::3]  # material index in the cell

        # Hits in all non-void cells
        s1 = 0  # hits in all cells, for check only
        s2 = 0  # hits in non-void cells
        for ic in range(nc):
            s1 += hl[ic]
            if ml[ic] != 0:
                s2 += hl[ic]
        assert s1 == nh
        if 0 in ml:
            assert s2 < nh
        else:
            assert s2 == nh

        a[i - 1, j - 1, k - 1] = float(s2) / float(nh)
    return x, y, z, a
