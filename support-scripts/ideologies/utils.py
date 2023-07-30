import os
import sys


CWD = os.path.join(os.path.dirname(sys.argv[0]))


def save_file_pdx(full_path, text):
    with open(full_path, "w", encoding="utf-8-sig") as f:
        f.write(text)
