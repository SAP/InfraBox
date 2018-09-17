import os

IB_DEFAULT_FILENAMES = ['infrabox.json', 'infrabox.yaml']

def find_infrabox_file(base_dir):
    ib_files = [os.path.join(base_dir, filename) for filename in IB_DEFAULT_FILENAMES]
    for ib_file in ib_files:
        if os.path.isfile(ib_file):
            return ib_file
    return None
