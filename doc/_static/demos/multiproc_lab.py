import argparse
import multiprocessing as mp
import time
import uuid
import rpy2.rinterface as ri
import rpy2.rinterface_lib.embedded

R_ID_TAG = '_rpy2_R_id_'


def print_setup(args):
    print('-'*28)
    print(f'Worker type        : {args.worker}')
    print(f'number or procs    : {args.nproc}')
    print(f'number of tasks    : {args.ntask}')
    print(f'max tasks per child: {args.maxtasksperchild}')
    print('-'*28)


def initializer():
    if rpy2.rinterface_lib.embedded.isready():
        print('R is is already initialized!')
    ri.initr()
    # Add other R initialization code here.
    # Loading R packages can have a very significant
    # influence on the time to initialize.


def tag_r(r_id):
    if R_ID_TAG in ri.globalenv:
        print('This embedded R has already been used (has a state).')
    ri.globalenv[R_ID_TAG] = r_id


def keys_globalenv():
    return tuple(ri.globalenv.keys())


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description=('Test the effect of various combinations of '
                     'parameters to run several R in parallel using '
                     'Python multiprocessing.'))
    parser.add_argument('--worker',
                        required=True,
                        choices=('fork', 'spawn'),
                        default='spawn',
                        help=('Type of worker process. You probably want '
                              '"spwan"'))
    parser.add_argument('--nproc',
                        default=3,
                        type=int,
                        help='Number or processes.')
    parser.add_argument('--ntask',
                        default=2,
                        type=int,
                        help='Number of (imaginary) tasks to process.')
    parser.add_argument('--maxtasksperchild',
                        default=1,
                        type=int,
                        help=('Maximum number of tasks per child process. '))
    args = parser.parse_args()

    print_setup(args)

    t0 = time.time()
    pool = (mp.get_context(args.worker)
            .Pool(processes=args.nproc,
                  initializer=initializer,
                  maxtasksperchild=args.maxtasksperchild))
    t1 = time.time()

    worker_ids = tuple(str(uuid.uuid4()) for _ in range(args.ntask))
    res = pool.map(tag_r, worker_ids)
    t2 = time.time()

    print('{0:.5f} seconds in total'.format(t2-t1))
    print('{0:.5f} seconds per task'.format((t2-t1)/args.ntask))
