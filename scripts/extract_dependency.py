import argparse
import tomllib


def read_pyproject(path):
    with open(path, 'rb') as fh:
        pyproject = tomllib.load(fh)
    return pyproject


def extract_dependency(pyproject, dependency):
    res = []
    for item in pyproject['project']['dependencies']:
        if item.startswith(dependency):
            res.append(item)
    if len(res) == 0:
        raise ValueError('No dependency found.')
    elif len(res) > 1:
        raise ValueError(f'More than one matching dependency found: {res}')
    return res


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('dependency')
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    pyproject = read_pyproject(args.path)
    res = extract_dependency(pyproject, args.dependency)
    print(res[0])


if __name__ == '__main__':
    main()
