import SocketServer
import sys, struct, pickle, cStringIO
import rpy2.robjects as robjects

class MessageElement(object):
    def __init__(self, stream):
        #size = struct.unpack('>Q', stream.read(8))
        self.object = pickle.load(stream)

class Message(object):
    def __init__(self, stream):
        self._stream = stream
        self.cmd = self._stream.read(10).split('\x00')[0]
            
    def __iter__(self):
        while True:
            try:
                res = MessageElement(self._stream)
            except Exception:
                raise StopIteration()
            yield res

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
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        print "message from IP:%s" % self.client_address[0]
        message = Message(self.rfile)
        if message.cmd == "CMD_eval":
            it = iter(message)
            rfunction = it.next().object
            if type(rfunction) == str:
                rfunction = robjects.globalenv.get(rfunction)
            parameters = tuple(x.object for x in it)
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

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((options.host, options.port), MyTCPHandler)
    print("Listening on port %i" % options.port)
    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()

