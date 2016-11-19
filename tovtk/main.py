#!/usr/bin/env python

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

from sys import argv
import vtk
_vtkVersion = vtk.vtkVersion.GetVTKSourceVersion().split()[-1]
from .tallies import read_meshtal
from numpy import array, reshape

def main():

    if len(argv) == 1:
        print help_note
        return
    else:
        mfiles = argv[1:]

    # normalize to 400 W
    # c1 = 3.1567674e6 # W/MeV
    c1 = (400e6              # Kinetic neutron power, W
        * (40.0/360.0)      # 40 grad sector
        / 14.0791)           # mean neutron energy, MeV
    c2 = c1 / 1.60218e-13   # Conversion factor, J/MeV

    print normalization_note.format(c1, c2)

    # mb = vtk.vtkMultiBlockDataSet()
    # af = vtk.vtkAppendFilter()
    #
    # nblocks = 0
    for meshtal in mfiles:
        print 'Reading ', meshtal,

        title, nps, td = read_meshtal(meshtal, use_uncertainties=False)
        print 'complete'

        for tn, t  in td.items():
            if t.geom.lower() not in ('xyz', 'rect'):
                continue

            vals = array(t.values)
            errs = array(t.errors)

            # reshape arrays, to account for energy bins:
            sh = (len(t.emesh), len(t.imesh), len(t.jmesh), len(t.kmesh))
            rvals = reshape(vals, sh)
            rerrs = reshape(errs, sh)

            # prepare grid boundaries
            x = vtk.vtkDoubleArray()
            y = vtk.vtkDoubleArray()
            z = vtk.vtkDoubleArray()
            x.SetName('x')
            y.SetName('y')
            z.SetName('z')
            for a, i0, l in ((x, t.origin.x, t.imesh),
                             (y, t.origin.y, t.jmesh),
                             (z, t.origin.z, t.kmesh)):
                for v in [i0] + l:
                    a.InsertNextValue(v)


            # put boundaries and data into VTK rectilinear grid
            grid = vtk.vtkRectilinearGrid()
            grid.SetDimensions(x.GetNumberOfTuples(),
                               y.GetNumberOfTuples(),
                               z.GetNumberOfTuples())
            grid.SetXCoordinates(x)
            grid.SetYCoordinates(y)
            grid.SetZCoordinates(z)


            # prepare array for tally values and errors
            # Value and error will be rwitten as separate scalar arrays. In this form the threshold
            # filter can be applied in paraview. This filter cannot be applied to an array of vectors.
            val = vtk.vtkDoubleArray()

            # Data arrays containing values and errors should heve the same name
            # for all datasets. In this case it is more simple to replace one data
            # set with another one in the paraview state. WHen datasets have
            # different names, one needs to change data arrays to be displayed
            # manually for all views.

            # val.SetName('{} t{} val'.format(meshtal, tn))
            # val.SetName('t{} val'.format(tn))
            val.SetName('val')
            val.SetNumberOfComponents(1)
            val.SetNumberOfTuples(grid.GetNumberOfCells())

            err = vtk.vtkDoubleArray()
            # err.SetName('{} t{} err'.format(meshtal, tn))
            # err.SetName('t{} err'.format(tn))
            err.SetName('err')
            err.SetNumberOfComponents(1) # value and rel.err.
            err.SetNumberOfTuples(grid.GetNumberOfCells())

            # Put tally results to values array in particular order
            xlen = x.GetNumberOfTuples()-1
            ylen = y.GetNumberOfTuples()-1
            zlen = z.GetNumberOfTuples()-1
            ival = 0 # index for meshtal
            vmax = max(t.values)
            vmin = vmax
            for i in range(xlen):
                for j in range(ylen):
                    for k in range(zlen):
                        idx = grid.ComputeCellId((i, j, k))
                        # hn = t.values[ival]
                        # en = t.errors[ival]
                        hn = rvals[-1, i, j, k]
                        en = rerrs[-1, i, j, k]


                        # Replace zero values and zero errors with NaN:
                        if en > 0:
                            # compute non-negative min
                            if hn < vmin:
                                vmin = hn
                        # else:
                        #     # Replace zero values
                        #     hn = -1.0
                        #     en = -1.0

                        val.SetTuple(idx, (hn, ))
                        err.SetTuple(idx, (en, ))
                        ival += 1

            # Field data to store meshtal metadata
            df = vtk.vtkStringArray()
            df.SetName('Meshtal description')
            df.SetNumberOfTuples(4)
            df.SetValue(0, 'Meshtal file {}, tally {}'.format(meshtal, tn))
            df.SetValue(1, title)
            df.SetValue(2, str(nps))
            df.SetValue(3, 'min: {}, max: {}'.format(vmin, vmax))

            # Attach values to the grid
            grid.GetCellData().AddArray(val)
            grid.GetCellData().AddArray(err)
            grid.GetFieldData().AddArray(df)

            # # Attach current grid to multigrid
            # mb.SetBlock(nblocks, grid)
            # af.AddInputData(grid)
            # nblocks += 1

            # write to file:
            writer = vtk.vtkXMLRectilinearGridWriter()
            if _vtkVersion[0] == '6':
                writer.SetInputData(grid)
            else:
                # _vtkVersion[0] == '5':
                writer.SetInput(grid)
            writer.SetFileName('{}_t{}.vtr'.format(meshtal, tn))
            ws = writer.Write()
            if ws == 1:
                print 'Tally {} from {}: non-negative range from {:12.5e} to {:12.5e}'.format(tn, writer.GetFileName(), vmin, vmax)
            else:
                print 'Failed to write meshtally {} from {}'.format(tn, writer.GetFileName())


if __name__ == '__main__':
    main()

