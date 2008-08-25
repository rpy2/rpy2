
def default_cmp(x, y):
    """ Default comparison function """
    if x < y: 
        return -1
    elif x > y:
        return +1
    else:
        return 0

def order(seq, cmp = default_cmp, reverse = False):
    """ Return the order in which to take the items to obtained
    a sorted sequence."""
    o = range(len(seq))

    def wrap_cmp(x, y):
        x = seq[x]
        y = seq[y]
        return cmp(x, y)
        
    o.sort(cmp = wrap_cmp, reverse = reverse)

    return o


