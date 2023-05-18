#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from typing import List

import regex

ap = argparse.ArgumentParser(
    "detect_contextfree_logs.py",
    "./detect_contextfree_logs.py dir",
    "This detects logs without context where one is around. Warnings can be ignored by '//nolint:ctxfreelogs'.",
    "Example: ./detect_contextfree_logs.py dir -E 'vendor/.*' -E '.*test.go'",
)
ap.add_argument("dir", help="Dir containing go files")
ap.add_argument(
    "-E",
    "--exclude",
    action="append",
    help="Exclude files that match the given regex pattern. Multiple exclude patterns can be specified.",
)
args = ap.parse_args()
excludes: List[regex.Regex] = [regex.compile(r) for r in args.exclude]
stmt_func = regex.compile("""^\\s*func .*ctx context\\.Context""")
stmt_log = regex.compile("""^\\s+log""")
valid_words = [
    "Context",
    "ctx"
]


def find_contextfree_lines(filepath: str, lines: List[str]) -> List[int]:
    ret = []
    in_func = False
    has_first = False
    left_bracket = 0
    for i, line in enumerate(lines):
        if not stmt_func.match(line) and not in_func:
            continue
        if stmt_func.match(line) and not in_func:
            in_func = True
        if stmt_log.search(line) and not any(w in line for w in valid_words):
            ret.append(i)

        for c in line:
            if c == "{":
                has_first = True
                left_bracket += 1
            elif c == "}":
                left_bracket -= 1

        if left_bracket < 0:
            print(f"{filepath}:{i} left_bracket < 0")
            sys.exit(1)
        if left_bracket == 0 and has_first:
            in_func = False
            has_first = False

    return ret


def do(filepath):
    with open(filepath) as file:
        lines = [line.rstrip() for line in file.readlines()]
    bes = find_contextfree_lines(filepath, lines)
    for n in bes:
        print(f"{filepath}:{n} {lines[n]}")


def traverse(dir) -> List[str]:
    ret = []
    for root, _, files in os.walk(dir):
        for f in files:
            filepath = os.path.join(root, f)
            if os.path.splitext(filepath)[-1] != ".go" or any(i.search(filepath) for i in excludes):
                continue
            ret.append(filepath)
    return ret


if __name__ == "__main__":
    fs = traverse(args.dir)
    for f in fs:
        do(f)
