#/usr/bin/env python

"""
Illustrate necessity to use ComputeCellId((i, j, k))
to get particular cell index.
"""
import vtk
import numpy

def vtkDA(N):
    """
    Returns a new vtkDoubleArray containing N elements
    """
    r = vtk.vtkDoubleArray()
    r.SetNumberOfTuples(N)

    for i in xrange(N):
        r.SetTuple(i, (i, ))

    return r

def npyDA(N):
    """
    Returns a new numpy array containing N elements
    """
    r = numpy.array(xrange(N))
    return r


if __name__ == '__main__':
    # test vtkDA
    from sys import argv
    n = int(argv[1])
    t = argv[2]
    if "vtk" in t:
        r = vtkDA(n)
    elif "numpy" in t:
        r = npyDA(n)


