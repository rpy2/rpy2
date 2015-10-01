import socket
import sys
import locale
import argparse


def send_R_code(rcode, hostname, port):
    """
    Evaluate the R code in `rcode` (on a possibly remote machine)
    """
    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to server and send data
    sock.connect((hostname, port))
    size_send = len(rcode).to_bytes(8, 'little')
    sock.send(bytes(encoding, 'ASCII') + b'\n' + \
              size_send + \
              rcode)

    # Receive data from the server and shut down
    print("Received:")
    size = int.from_bytes(sock.recv(8), 'little') # 64 bits max
    print("    size: %i bytes" % size)
    received = sock.recv(size)
    sock.close()
    print("    R output:")
    print(str(received, encoding))


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port',
                        type=int,
                        default=8080)
    parser.add_argument('--hostname',
                        default='localhost')
    
    options = parser.parse_args()

    # read R code from STDIN
    rcode = sys.stdin.read()
    encoding = locale.getlocale()[1]
    rcode = bytes(rcode, encoding)

    send_R_code(rcode, options.hostname, options.port)
