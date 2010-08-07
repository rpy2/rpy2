
import random
import time
import sys
import array
import numpy
import rpy2.robjects as ro


sys.stdout.write("Setting up...")
n = 20000
n_loop = 100
x_list = [random.random() for i in xrange(n)]
x_array = array.array('f', x_list)
x_numpy = numpy.array(x_list, 'f')
x_floatvector = ro.FloatVector(x_list)
x_sexpvector = ro.rinterface.SexpVector(x_floatvector)
sys.stdout.write("done.\n")

r_loopsum = """
function(x) { total = 0; for (elt in x) {total <- total + elt} }
"""
ro.globalenv['x'] = x_floatvector
rdo_loopsum = """
for (i in 1:%i) {
  res <- %s(x)
}
"""

ro.globalenv['r_sum'] = ro.r(r_loopsum)

def python_reduce(x):
    total = reduce(lambda x, y: x+y, x)
    return total

def python_sum(x):
    total = 0.0
    for elt in x:
        total += elt
    return total


def run_test(f, x):
    begin = time.time()
    for i in xrange(n_loop):
        res = f(x)
    end = time.time()
    return end-begin

begin = time.time()
ro.r(rdo_loopsum %(n_loop, "r_sum"))
end = time.time()
rpure_time = end-begin
print("pure R - :%f" %rpure_time)
begin = time.time()
ro.r(rdo_loopsum %(n_loop, "sum"))
end = time.time()
rbuiltin_time = end-begin
print("builtin R - :%f" %(1/(rbuiltin_time/rpure_time)))


combos = [(label_function, function, label_sequence, sequence) \
          for label_function, function in (("pure python", python_sum), \
                                           ("reduce python", python_reduce), \
                                           ("builtin python", sum))
          for label_sequence, sequence in (("SexpVector", x_sexpvector), \
                                           ("FloatVector", x_floatvector),
                                           ("list", x_list),
                                           ("array", x_array),
                                           ("numpy.array", x_numpy))]
res = []
for label_function, function, label_sequence, sequence in combos:
    res.append(run_test(function, sequence))
    print("%s - %s: %f" %(label_function, label_sequence, 1/(res[-1]/rpure_time)))


tmp = run_test(x_numpy.sum, None)
print("%s - %s: %f" %("numpy.array.sum", "numpy.array", 1/(tmp/rpure_time)))




