import argparse
import os
import json

def main():
    parser = argparse.ArgumentParser(description='Check expected result')
    parser.add_argument('test_dir', type=string, help='Directory of the test')
    parser.add_argument('output_file', type=string, help='Directory of the test')

    args = parser.parse_args()

    expected_path = os.path.join(args.test_dir, "expected.json")
    if not os.path.exists(expected_path):
        raise Exception("%s does not exist")

    with open(expected_path) as f:
        e = json.load(f)

    if not os.path.exists(args.output_file):
        raise Exception("%s does not exist")

    #with open(args.output_file) as fo:
    #    output = fo.read








if __name__ == "__main__":
    main()
