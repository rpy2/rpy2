import SocketServer
import sys
import rpy2.robjects as robjects

class MyTCPHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.data = self.rfile.readline().strip()

        # verbose server
        print "%s wrote:" % self.client_address[0]
        print self.data

        # evaluate the data passed as a string of R code
        results = robjects.r(self.data)

        # return the result of the evaluation as a string
        # to the client
        self.wfile.write(str(results))


if __name__ == "__main__":
    HOST, PORT = "localhost", int(sys.argv[1])

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
