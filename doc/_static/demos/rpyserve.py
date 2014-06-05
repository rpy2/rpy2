import SocketServer, sys, struct, pickle, cStringIO
import rpy2.robjects as robjects

def iter_arguments(stream):
    while True:
        try:
            res = pickle.load(stream)
            yield res
        except Exception:
            raise StopIteration()

def conversion(object):
    if isinstance(object, robjects.vectors.Vector):
        if isinstance(object, robjects.vectors.ListVector):
            return tuple(conversion(x) for x in object)
        else:
            return tuple(object)
    else:
        raise ValueError("Currently only vectors are supported.")

class MyTCPHandler(SocketServer.StreamRequestHandler):
    timeout = 2
    def handle(self):
        print "Received message from IP:%s" % self.client_address[0]
        cmd = self.rfile.read(10).split('\x00')[0]
        if cmd == "CMD_eval":
            m_iter = iter_arguments(message)
            rfunction = m_iter.next()
            if type(rfunction) == str:
                rfunction = robjects.globalenv.get(rfunction)
            parameters = tuple(x for x in m_iter)
            # evaluate the call
            results = rfunction(*parameters)
            # build the message to return
            self.wfile.write(struct.pack("10s", "data"))
            data = pickle.dumps(conversion(results))
            self.wfile.write(struct.pack(">Q", len(data)))
            self.wfile.write(data)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description = 'RServe-like server')
    parser.add_argument('-H', default = "localhost", dest = 'host', help = 'Host')
    parser.add_argument('-P', required = True, type = int, dest = 'port', help = 'Port')
    options = parser.parse_args()

    # Create the server
    server = SocketServer.TCPServer((options.host, options.port), MyTCPHandler)
    print("Listening on port %i" % options.port)
    # Activate the server; this will keep running until interrupted or Ctrl-C
    server.serve_forever()

