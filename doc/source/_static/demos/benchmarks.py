import random
import time
import sys
import itertools
import multiprocessing
import array, numpy, rpy2.robjects as ro
from rpy2.robjects import Formula

n_loops = (1, 10, 20, 30, 40)

def setup_func(kind):
#-- setup_sum-begin
    n = 20000
    x_list = [random.random() for i in xrange(n)]
    module = None
    if kind == "array.array":
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
        res = module.rinterface.IntSexpVector(x_list)
        module.globalenv['x'] = res
        res = None
#-- setup_sum-end
    else:
        raise ValueError("Unknown kind '%s'" %kind)
    return (res, module)


def python_reduce(x):
    total = reduce(lambda x, y: x+y, x)
    return total


#-- purepython_sum-begin
def python_sum(x):
    total = 0.0
    for elt in x:
        total += elt
    return total
#-- purepython_sum-end

def test_sumr(queue, func, n, setup_func):
    array, module = setup_func("R")
    r_loopsum = """
#-- purer_sum-begin
function(x)
{
  total = 0;
  for (elt in x) {
    total <- total + elt
  } 
}
#-- purer_sum-end
"""
    
    rdo_loopsum = """
f <- %s
for (i in 1:%i) {
  res <- f(x)
}
"""
    rcode = rdo_loopsum %(r_loopsum, n)
    time_beg = time.time()
    #print(rcode)
    module.r(rcode)
    time_end = time.time()
    queue.put(time_end - time_beg)

def test_sumr_compile(queue, func, n, setup_func):
    array, module = setup_func("R")
    r_loopsum = """
#-- purer_sum-begin
function(x)
{
  total = 0;
  for (elt in x) {
    total <- total + elt
  } 
}
#-- purer_sum-end
"""
    
    rdo_loopsum = """
f <- %s
for (i in 1:%i) {
  res <- f(x)
}
"""
    compiler = ro.packages.importr("compiler")
    rcode = rdo_loopsum %("compiler::compile("+r_loopsum+")", n)
    time_beg = time.time()
    #print(rcode)
    module.r(rcode)
    time_end = time.time()
    queue.put(time_end - time_beg)


def test_sum(queue, func, array_type, n, setup_func):
    array, module = setup_func(array_type)
    time_beg = time.time()
    for i in xrange(n):
        res = func(array)
    time_end = time.time()
    queue.put(time_end - time_beg)

q = multiprocessing.Queue()
combos = [(label_func, func, label_sequence, n_loop) \
          for label_func, func in (("pure python", python_sum), \
                                   ("reduce python", python_reduce), \
                                   ("builtin python", sum))
          for label_sequence in ("SexpVector",
                                 "FloatVector",
                                 "list",
                                 "array.array",
                                 "numpy.array")
          for n_loop in n_loops]

times = []
# python
for label_func, func, label_sequence, n_loop in combos:
    p = multiprocessing.Process(target = test_sum, args = (q, func,
                                                           label_sequence,
                                                           n_loop,
                                                           setup_func))
    p.start()
    res = q.get()
    p.join()
    times.append(res)


combos_r = [(label_func, None, None, n_loop) \
                for label_func, func in (("R", None), \
                                             ("R compiled", None))            
            for n_loop in n_loops]

times_r = []
# pure R
for n_loop in n_loops:
    p = multiprocessing.Process(target = test_sumr, args = (q, func,
                                                            n_loop,
                                                            setup_func))
    p.start()
    res = q.get()
    p.join()
    times_r.append(res)

# pure R compiled
for n_loop in n_loops:
    p = multiprocessing.Process(target = test_sumr_compile, 
                                args = (q, func,
                                        n_loop,
                                        setup_func))
    p.start()
    res = q.get()
    p.join()
    times_r.append(res)



from rpy2.robjects.vectors import DataFrame, FloatVector, StrVector, IntVector
d = {}
d['code'] = StrVector([x[0] for x in combos]) + StrVector([x[0] for x in combos_r])
d['sequence'] = StrVector([x[-2] for x in combos]) + StrVector([x[0] for x in combos_r])
d['time'] = FloatVector([x for x in times]) + FloatVector([x[0] for x in combos_r])
d['n_loop']    = IntVector([x[-1] for x in combos]) + IntVector([x[1] for x in combos_r])
d['group'] = StrVector([d['code'][x] + ':' + d['sequence'][x] for x in xrange(len(d['n_loop']))])
dataf = DataFrame(d)



from rpy2.robjects.lib import ggplot2
p = ggplot2.ggplot(dataf) + \
    ggplot2.geom_line(ggplot2.aes_string(x="n_loop", 
                                         y="time",
                                         colour="code")) + \
    ggplot2.geom_point(ggplot2.aes_string(x="n_loop", 
                                          y="time",
                                          colour="code")) + \
    ggplot2.facet_wrap(Formula('~sequence')) + \
    ggplot2.scale_y_continuous('running time') + \
    ggplot2.scale_x_continuous('repeated n times', ) + \
    ggplot2.xlim(0, max(n_loops)) + \
    ggplot2.opts(title = "Benchmark (running time)")


from rpy2.robjects.packages import importr
grdevices = importr('grDevices')
grdevices.png('../../_static/benchmark_sum.png',
              width = 712, height = 512)
p.plot()
grdevices.dev_off()

#base = importr("base")
stats = importr('stats')
nlme = importr("nlme")
fit = nlme.lmList(Formula('time ~ n_loop | group'), data = dataf, 
                  na_action = stats.na_exclude)


# scale to R's slope
speedup = [1/x for x in stats.coef(fit).rx2("n_loop").ro / stats.coef(fit).rx("R:R", True)[1][0]]

# workaround an issue in class mapping
df = DataFrame(stats.coef(fit))

import os
pad_len = (15, 45, 10)
header = ("Function", "Sequence", "Speedup")
res = [' '.join(["=" * pad_len[x] for x in range(3)]),
       ' '.join([header[x].ljust(pad_len[x]) for x in range(3)]),
       ' '.join(["=" * pad_len[x] for x in range(3)])]
for coef_name, sp in itertools.izip(df.rownames, speedup):
    row_content = coef_name.split(':')
    row_content.append('%.2f' %sp)
    res.append(' '.join([row_content[x].ljust(pad_len[x]) for x in range(3)]))
res.append(' '.join(["=" * pad_len[x] for x in range(3)]))
print(os.linesep.join(res))

