import random
import time
import sys
import multiprocessing
import array, numpy, rpy2.robjects as ro



def setup_func(kind):
    n = 20000
    x_list = [random.random() for i in xrange(n)]
    module = None
    if kind == "array":
        import array as module
        res = module.array('f', x_list)
    elif kind == "numpy.array":
        import numpy as module
        res = module.array(x_list, 'f')
    elif kind == "FloatVector":
        import rpy2.robjects as module
        res = module.FloatVector(x_list)
    elif kind == "SexpVector":
        import rpy2.rinterface as module
        module.initr()
        res = module.IntSexpVector(x_list)
    elif kind == "list":
        res = x_list
    elif kind == "R":
        import rpy2.robjects as module
        res = module.IntVector(x_list)
        module.globalenv['x'] = res
        res = None
    else:
        raise ValueError("Unknown kind '%s'" %kind)
    return (res, module)


def python_reduce(x):
    total = reduce(lambda x, y: x+y, x)
    return total



def python_sum(x):
    total = 0.0
    for elt in x:
        total += elt
    return total

def test_sum(queue, func, array_type, n, setup_func):
    array, module = setup_func(array_type)
    time_beg = time.time()
    for i in xrange(n):
        res = func(array)
    time_end = time.time()
    queue.put(time_end - time_beg)

q = multiprocessing.Queue()
combos = [(label_func, func, label_sequence) \
          for label_func, func in (("pure python", python_sum), \
                                   ("reduce python", python_reduce), \
                                   ("builtin python", sum))
          for label_sequence in ("SexpVector",
                                 "FloatVector",
                                 "list",
                                 "array",
                                 "numpy.array")]

times = []
n_loop = 100



# python
for label_func, func, label_sequence in combos:
    p = multiprocessing.Process(target = test_sum, args = (q, func,
                                                           label_sequence,
                                                           n_loop,
                                                           setup_func))
    p.start()
    res = q.get()
    p.join()
    times.append(res)


# pure R
def test_sumr(queue, func, n, setup_func):
    array, module = setup_func("R")
    time_beg = time.time()
    r_loopsum = """
function(x) { total = 0; for (elt in x) {total <- total + elt} }
"""
    
    rdo_loopsum = """
for (i in 1:%i) {
  res <- %s(x)
}
"""
    module.r(rdo_loopsum %(n, r_loopsum))
    time_end = time.time()
    queue.put(time_end - time_beg)

p = multiprocessing.Process(target = test_sumr, args = (q, func,
                                                        n_loop,
                                                        setup_func))
p.start()
res = q.get()
p.join()
times.append(res)
combos.append(("R", None, "R"))




from rpy2.robjects.vectors import DataFrame, FloatVector, StrVector
d = {}
d['code'] = StrVector([x[0] for x in combos])
d['sequence'] = StrVector([x[-1] for x in combos])
d['time'] = FloatVector([x for x in times])

dataf = DataFrame(d)

from rpy2.robjects.lib import ggplot2
p = ggplot2.ggplot(dataf) + \
    ggplot2.geom_point(ggplot2.aes_string(x="sequence", 
                                          y="time", 
                                          colour="code"))
p.plot()
