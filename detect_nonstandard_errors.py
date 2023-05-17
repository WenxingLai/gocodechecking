#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import subprocess
from typing import List

import regex

ap = argparse.ArgumentParser(
    "detect_nonstandard_errors.py",
    "./detect_nonstandard_errors.py dir",
    "This detects if-err statements which does not satisfy Rule 2.5.1 of https://git.woa.com/standards/go.",
    "Example: ./detect_nonstandard_errors.py dir -E 'vendor/.*'"
)

ap.add_argument("dir", help="Dir containing go files")
ap.add_argument(
    "-E",
    "--exclude",
    action="append",
    help="Exclude files that match the given regex pattern. Multiple exclude patterns can be specified.",
)

args = ap.parse_args()
excludes = [regex.compile(r) for r in args.exclude]

valid_stmts = [
    regex.compile(regex.compile("""//nolint:.*standarderr"""),)
]

def do(filepath: str):
    cmds = [
        ["grep", "-rnEH", "'^\\s+if +[a-zA-Z]?[eE]rr\\W+!=\\W+nil\\W+[|&]{2}'", filepath],
        ["grep", "-rnEH", "'^\\s+if +[a-zA-Z]?[eE]rr\\W+=='", filepath],
    ]
    for cmd in cmds:
        result = subprocess.run(" ".join(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        msg = result.stdout.decode("utf-8").rstrip()
        if not msg:
            continue
        if any(r.search(msg) for r in valid_stmts):
            continue
        print(msg)


def traverse(dir) -> List[str]:
    ret = []
    for root, _, files in os.walk(dir):
        for f in files:
            filepath = os.path.join(root, f)
            if os.path.splitext(filepath)[-1] != ".go" or any([i.search(filepath) for i in excludes]):
                continue
            ret.append(filepath)
    return ret


if __name__ == "__main__":
    fs = traverse(args.dir)
    for f in fs:
        do(f)
