from distutils.core import setup

setup(name = 'tovtk',
      version = '1.3.0',
      description = 'Python meshtal to vtk converter',
      author = 'A. Travleev, INR-KIT',
      author_email = 'anton.travleev@kit.edu',
      packages = ['tovtk', ],
      entry_points = {'console_scripts': ['tovtk = tovtk.main:main']},
      )


