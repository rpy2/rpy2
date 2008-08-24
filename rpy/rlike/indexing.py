
def order(sortable, reverse = False):
    o = range(len(sortable))
    def cmp(x, y):
        x = sortable[x]
        y = sortable[y]
        if x < y: 
            return -1
        elif x > y:
            return +1
        else:
            return 0
        
    o.sort(cmp = cmp, reverse = reverse)

    return o


