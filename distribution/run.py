'''
Created on Nov 24, 2011

@package: Superdesk
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the deployment of the distribution that contains this deploy.
'''

from types import ModuleType
import argparse
import os
import sys
import time
import timeit
import traceback

# --------------------------------------------------------------------

if __name__ == '__main__':
    # First we need to set the working directory relative to the application deployer just in case the application is
    # started from somewhere else
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    def findLibraries(folder):
        '''Finds all the libraries (that have extension .egg or are folders) if the provided folder'''
        if os.path.isdir(folder): return (os.path.join(folder, name) for name in os.listdir(folder))
        return ()

    # Loading the libraries
    for path in findLibraries('libraries'):
        if path not in sys.path: sys.path.append(path)

    # Loading the components.
    for path in findLibraries('components'):
        if path not in sys.path: sys.path.append(path)

    try: import ally_start
    except ImportError:
        print('Corrupted or missing ally component, make sure that this component is not missing from python path '
              'or components eggs', file=sys.stderr)
        sys.exit(1)
    deployTime = timeit.timeit(ally_start.__deploy__, number=1)
    print('=' * 50, 'Application deployed in %.2f seconds' % deployTime)
