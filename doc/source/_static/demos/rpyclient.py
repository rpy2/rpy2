import socket
import sys, struct, cStringIO, pickle

HOST, PORT = sys.argv[1].split(":")
PORT = int(PORT)
data = " ".join(sys.argv[2:])

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server and send data
sock.connect((HOST, PORT))

message = cStringIO.StringIO()
message.write(struct.pack('10s', 'CMD_eval'))
# The R call to make is `rnorm(10)`
func_name = 'rnorm'
pickle.dump(func_name, message)
pickle.dump(10, message)
sock.send(message.getvalue())

# Receive data from the server and shut down
cmd = sock.recv(10).split('\x00')[0]
size = struct.unpack(">Q", sock.recv(8))[0]
data = pickle.loads(sock.recv(size))
sock.close()

