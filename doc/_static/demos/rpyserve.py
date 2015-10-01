import socketserver
import sys
import rpy2.robjects as robjects

class MyTCPHandler(socketserver.StreamRequestHandler):

    def handle(self):
        # verbose server
        print("%s wrote:" % self.client_address[0])

        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        encoding = self.rfile.readline().strip()
        encoding = str(encoding, 'ASCII')
        print('    encoding: %s' % encoding)

        size = int.from_bytes(self.rfile.read(8), 'little')
        print('    size: %i bytes' % size)
        
        rcv = self.rfile.read(size)
        rcv = str(rcv, encoding) 

        # verbose server
        print('    R code string:')
        print(rcv)

        # evaluate the data passed as a string of R code
        results = robjects.r(rcv)

        # return the result of the evaluation as a string
        # to the client
        results = bytes(str(results), encoding)
        size_res = len(results).to_bytes(8, 'little')
        print('    Result size: %i' % len(results))
        self.wfile.write(size_res +
                         results)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', 
                        type=int,
                        default=8080,
                        help='port')
    parser.add_argument('--hostname',
                        default='localhost')
    options = parser.parse_args()

    # Create the server, binding to localhost on port 9999
    server = socketserver.TCPServer((options.hostname, options.port),
                                    MyTCPHandler)

    print('Server listening on %s:%i' % (options.hostname, options.port))
    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
