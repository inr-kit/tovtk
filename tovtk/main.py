#!/usr/bin/env python

from sys import argv
import vtk
from numpy import array, reshape, amax, amin
from .tallies import read_meshtal
from .dgs import readdgs, readdgs_old

_vtkVersion = vtk.vtkVersion.GetVTKSourceVersion().split()[-1]

help_note = """
Meshtal to VTK converter.

Converts rectangular meshtallies from meshtal files given in the command line.
Each meshtally is written to a separate vtr file representing a rectilinear
grid. Invocation:

    >tovtk  meshtal1 [meshtal2 ...]

For each meshtally `N` in file `meshtal`, script writes a vtk file named
`meshtal_tN.vtr`.  """

normalization_note = """
Normalization constants not applied, generated vtk files contain data
exactly as in meshtal files. For ITER applications, normalization constants
for flux [1/cm2s] and heat [W/cm3]:

    Ch = {:18e}
    Cf = {:18e}

To normalize tallies in Paraview, use Programmable filter. For example, to
compute total heating from the neutron and photon components:

        v1 = inputs[0].CellData['val']
        v2 = inputs[1].CellData['val']

        output.CellData.append((v1 + v2)*Ch, 'Total heating')
"""


def rectangular(fname, xbounds, ybounds, zbounds, vals, errs=None, descr=[]):
    """
    Write rectangular data to file `fname`.

    Arrays xbounds, ybounds and zbounds are boundary coordinates.  Array `vals`
    is a 3-dimentional array of the shape (len(x)-1, len(y)-1, len(z)-1).

    Put strings from `descr` as description of the data.
    """
    # prepare grid boundaries
    x = vtk.vtkDoubleArray()
    y = vtk.vtkDoubleArray()
    z = vtk.vtkDoubleArray()
    x.SetName('x')
    y.SetName('y')
    z.SetName('z')
    for v in xbounds:
        x.InsertNextValue(v)
    for v in ybounds:
        y.InsertNextValue(v)
    for v in zbounds:
        z.InsertNextValue(v)

    # put boundaries and data into VTK rectilinear grid
    grid = vtk.vtkRectilinearGrid()
    grid.SetDimensions(x.GetNumberOfTuples(),
                       y.GetNumberOfTuples(),
                       z.GetNumberOfTuples())
    grid.SetXCoordinates(x)
    grid.SetYCoordinates(y)
    grid.SetZCoordinates(z)

    # prepare array for tally values and errors
    # Value and error will be rwitten as separate scalar arrays. In this form
    # the threshold filter can be applied in paraview. This filter cannot be
    # applied to an array of vectors.
    val = vtk.vtkDoubleArray()

    # Data arrays containing values and errors should heve the same name
    # for all datasets. In this case it is more simple to replace one data
    # set with another one in the paraview state. WHen datasets have
    # different names, one needs to change data arrays to be displayed
    # manually for all views.
    val.SetName('val')
    val.SetNumberOfComponents(1)
    val.SetNumberOfTuples(grid.GetNumberOfCells())

    if errs is not None:
        err = vtk.vtkDoubleArray()
        err.SetName('err')
        err.SetNumberOfComponents(1)
        err.SetNumberOfTuples(grid.GetNumberOfCells())

    # Put tally results to values array in particular order
    xlen = x.GetNumberOfTuples() - 1
    ylen = y.GetNumberOfTuples() - 1
    zlen = z.GetNumberOfTuples() - 1
    vmax = amax(vals[vals > 0.0])
    vmin = amin(vals[vals > 0.0])
    for i in range(xlen):
        for j in range(ylen):
            for k in range(zlen):
                idx = grid.ComputeCellId((i, j, k))
                hn = vals[i, j, k]
                if errs is not None:
                    en = errs[i, j, k]

                val.SetTuple(idx, (hn, ))
                if errs is not None:
                    err.SetTuple(idx, (en, ))

    # Field data to store metadata
    df = vtk.vtkStringArray()
    df.SetName('Description')
    df.SetNumberOfTuples(len(descr) + 2)
    df.SetValue(0, 'positive min: {}'.format(vmin))
    df.SetValue(1, 'positive max: {}'.format(vmax))
    for i, s in enumerate(descr):
        df.SetValue(i + 2, s)

    # Attach values to the grid
    grid.GetCellData().AddArray(val)
    if errs is not None:
        grid.GetCellData().AddArray(err)
    grid.GetFieldData().AddArray(df)

    # write to file:
    writer = vtk.vtkXMLRectilinearGridWriter()
    if _vtkVersion[0] == '6':
        writer.SetInputData(grid)
    else:
        # _vtkVersion[0] == '5':
        writer.SetInput(grid)
    writer.SetFileName(fname)
    ws = writer.Write()
    return ws


def main():

    if len(argv) == 1:
        print help_note
        return
    else:
        mfiles = argv[1:]

        # meshtal or dgs?
        if mfiles[0] == 'type=dgs':
            dtype = 'dgs'
            mfiles = mfiles[1:]
        elif mfiles[0] == 'type=dgs.old':
            dtype = 'dgs.old'
            mfiles = mfiles[1:]
        else:
            dtype = 'meshtal'

    # normalize to 400 W
    # c1 = 3.1567674e6 # W/MeV
    c1 = (400e6 *            # Kinetic neutron power, W
          (40.0/360.0) /     # 40 grad sector
          14.0791)           # mean neutron energy, MeV
    c2 = c1 / 1.60218e-13    # Conversion factor, J/MeV

    print normalization_note.format(c1, c2)

    if dtype == 'meshtal':
        for meshtal in mfiles:
            print 'Reading ', meshtal,

            title, nps, td = read_meshtal(meshtal, use_uncertainties=False)
            print 'complete'

            for tn, t in td.items():
                if t.geom.lower() not in ('xyz', 'rect'):
                    continue

                vals = array(t.values)
                errs = array(t.errors)

                # reshape arrays, to account for energy bins:
                sh = (len(t.emesh), len(t.imesh), len(t.jmesh), len(t.kmesh))

                if sh[0] > 1:
                    print 'Meshtally {} contains {} energy bins.'.format(tn, sh[0])
                    print 'Only "total" is written to vtk file'

                # Prepare array of values
                rvals = reshape(vals, sh)[-1, :, :, :]
                rerrs = reshape(errs, sh)[-1, :, :, :]
                # Prepare arrays of bin boundaries
                x = [t.origin.x] + t.imesh
                y = [t.origin.y] + t.jmesh
                z = [t.origin.z] + t.kmesh
                # Prepare description
                descr = []
                descr.append('Meshtal file {}, tally {}'.format(meshtal, tn))
                descr.append(title)
                descr.append('nps: {}'.format(nps))
                fname = '{}_t{}.vtr'.format(meshtal, tn)
                ws = rectangular(fname, x, y, z, rvals, errs=rerrs, descr=descr)

                if ws == 1:
                    print 'Tally {} written to {}'.format(tn, fname)
                else:
                    print 'Failed to write tally {} to {}'.format(tn, fname)
    elif dtype == 'dgs':
        for dgs in mfiles:
            print 'Reading ', dgs
            x, y, z, a = readdgs(dgs)
            fname = '{}.vtr'.format(dgs)
            ws = rectangular(fname, x, y, z, a, errs=None)
    elif dtype == 'dgs.old':
        for dgs in mfiles:
            print 'Reading ', dgs
            x, y, z, a = readdgs_old(dgs)
            fname = '{}.vtr'.format(dgs)
            ws = rectangular(fname, x, y, z, a, errs=None)


if __name__ == '__main__':
    main()
