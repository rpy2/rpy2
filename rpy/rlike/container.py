class NamedList(dict):
    """ Implements the Ordered Dict API defined in PEP 372.
    When `odict` becomes part of collections, this class 
    should inherit from it rather than from `dict`.

    This class differs a little from the Ordered Dict
    proposed in PEP 372 by the fact that:

    - not all elements have to be named. None has key value means
    an absence of name for the element.

    - unlike in R, all names are unique.

    """

    def __init__(self, c=[]):

        if isinstance(c, dict):
            #FIXME: allow instance from NamedList ?
            raise ValueError('A regular dictionnary does not ' +\
                                 'conserve the order of its keys.')

        super(NamedList, self).__init__()
        self.__l = []
        l = self.__l

        for k,v in c:
            self[k] = v


    def __cmp__(self, o):
        raise(Exception("Not yet implemented."))

    def __eq__(self):
        raise(Exception("Not yet implemented."))
        
    def __getitem__(self, key):
        if key is None:
            raise ValueError("Unnamed items cannot be retrieved by key.")
        i = super(NamedList, self).__getitem__(key)
        return self.__l[i][1]

    def __iter__(self):
        l = self.__l
        for e in l:
            k = e[0]
            if k is None:
                continue
            else:
                yield k

    def __len__(self):
        return len(self.__l)

    def __ne__(self):
        raise(Exception("Not yet implemented."))

    def __repr__(self):
        s = 'o{'
        for k,v in self.iteritems():
            s += "'" + str(k) + "': " + str(v) + ", "
        s += '}'
        return s

    def __reversed__(self):
        raise(Exception("Not yet implemented."))

    def __setitem__(self, key, value):
        """ Replace the element if the key is known, 
        and conserve its rank in the list, or append
        it if unknown. """

        if key is None:
            self.__l.append((key, value))
            return

        if self.has_key(key):
            i = self.index(key)
            self.__l[i] = (key, value)
        else:
            self.__l.append((key, value))
            super(NamedList, self).__setitem__(key, len(self.__l)-1)
            
    def byindex(self, i):
        """ Fetch a value by index (rank), rather than by key."""
        return self.__l[i]

    def index(self, k):
        """ Return the index (rank) for the key 'k' """
        return super(NamedList, self).__getitem__(k)

    def items(self):
        """ Return an ordered list of all key/value pairs """
        res = [self.byindex(i) for i in xrange(len(self.__l))]
        return res 

    def iteritems(self):
        return iter(self.__l)

    def reverse(self):
        """ Reverse the order of the elements in-place (no copy)."""
        l = self.__l
        n = len(self.__l)
        for i in xrange(n/2):
            tmp = l[i]
            l[i] = l[n-i-1]
            kv = l[i]
            if kv is not None:
                super(NamedList, self).__setitem__(kv[0], i)
            l[n-i-1] = tmp
            kv = tmp
            if kv is not None:
                super(NamedList, self).__setitem__(kv[0], n-i-1)
            

    def sort(self, cmp=None, key=None, reverse=False):
        raise(Exception("Not yet implemented."))

    
