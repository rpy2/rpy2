import unittest
from os.path import dirname

def main():
    tr = unittest.TextTestRunner(verbosity = 2)
    suite = unittest.TestLoader().discover(dirname(__file__))
    tr.run(suite)

if __name__ == '__main__':
    main()
