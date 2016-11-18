# tovtk
Python meshtal -> VTK converter.

Processes rectangular meshtallies. Output vtk files contain a rectilinear grid with cell values.

## Limitations
Only rectangular meshtally. 

In case `emesh` is used to split to energy bins, the resulting vtk file
contains values only from the total bin.

## Invocation

```bash
# Using the wrapper script:
>tovtk meshtal
# Using Python directly:
>pyhton -m tovtk meshtal
```

## Installation
Getting source from the github:
```bash
>mkdir tovtk-git
>cd tovtk-git
>git clone git@github.com:inr-kit/tovtk.git .
# with --user option does not require admin rights, 
# but PATH variable may need adjustments to point to 
# $HOME/.local/bin
>pip install --user -e .
# Or without the --user option. in this case requires admin rights
>sudo pip install -e .
```

## Dependensies
The tovtk package uses `numpy` and `vtk` Python bindings. In a recent ubuntu they can be
installed with 
```bash
>sudo apt-get install python-numpy
>sudo apt-get install python-vtk
```

Alternatively, Anaconda (https://www.continuum.io) includes numpy and vtk among many others.


