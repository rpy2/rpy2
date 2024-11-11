import argparse
import logging
from rpy2.situation import get_r_home
from rpy2.situation import iter_info
from rpy2.situation import r_ld_library_path_from_subprocess
from rpy2.situation import set_default_logging
import sys

logger = logging.getLogger(__name__)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        'Command-line tool to report the rpy2'
        'environment and help diagnose issues')
    parser.add_argument('action',
                        nargs='?',
                        choices=('info', 'LD_LIBRARY_PATH'),
                        default='info',
                        help=('Action to perform. "info" shows all info, '
                              'LD_LIBRARY_PATH returns optionally required '
                              'additions to the environment variable'))
    parser.add_argument('-v', '--verbose',
                        choices=('ERROR', 'WARNING', 'INFO', 'DEBUG'),
                        default='WARNING',
                        help=('Verbosity level. Options are given by '
                              'increasing order of verbosity '
                              '(defaut: %(default)s)'))
    args = parser.parse_args()
    logger.name = 'rpy2.situation'
    logger.setLevel(getattr(logging, args.verbose))
    set_default_logging()
    if args.action == 'info':
        for row in iter_info():
            print(row)
    elif args.action == 'LD_LIBRARY_PATH':
        r_home = get_r_home()
        if not r_home:
            print('R cannot be found in the PATH and RHOME cannot be found.')
            sys.exit(1)
        else:
            print(r_ld_library_path_from_subprocess(r_home))
