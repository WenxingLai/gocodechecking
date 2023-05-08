#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from typing import List, Tuple

import regex

ap = argparse.ArgumentParser(
    "detect_unconsumed_errors.py",
    "./detect_unconsumed_errors.py dir",
    "This detects errors unreturned and not logged. Warnings can be ignored by '//nolint:unconsumederr'.",
    "Example: ./detect_unconsumed_errors.py dir -E 'vendor/.*' -X 'Msg.*err'",
)
ap.add_argument("dir", help="Dir containing go files")
ap.add_argument(
    "-E",
    "--exclude",
    action="append",
    help="Exclude files that match the given regex pattern. Multiple exclude patterns can be specified.",
)
ap.add_argument(
    "-X",
    "--exclude-block-pattern",
    action="append",
    help="Exclude if blocks which contains a line matching the pattern. Multiple exclude patterns can be specified.",
)
args = ap.parse_args()
excludes: List[regex.Regex] = [regex.compile(r) for r in args.exclude]

stmt_if = regex.compile("""^\\W*if +err +!= +nil +\\{\\W*$""")
builtin_stmts = [
    regex.compile("""log.*err"""),
    regex.compile("""[pP]rint.*err"""),
    regex.compile("""Errorf.*err"""),
    regex.compile("""^\\W*return [a-zA-Z0-9, ]*err"""),
    regex.compile("""^\\W*panic.*err"""),
    regex.compile("""^\\W*os.Exit\\([0-9]+\\)"""),
    regex.compile("""//nolint:.*nilerr"""),
    regex.compile("""//nolint:.*unconsumederr"""),
]
user_stmts = [regex.compile(r) for r in args.exclude_block_pattern] if args.exclude_block_pattern else []
valid_stmts = builtin_stmts + user_stmts


def has_unconsumed_error(lines: List[str]) -> bool:
    for line in lines:
        for r in valid_stmts:
            if r.search(line):
                return False
    return True


def find_err_lines(filepath: str, lines: List[str]) -> List[Tuple[int, int]]:
    ret = []
    left_bracket = 0
    begin = 0
    for i, line in enumerate(lines):
        if not stmt_if.match(line) and left_bracket == 0:
            continue
        if stmt_if.match(line) and left_bracket == 0:
            left_bracket += 1
            begin = i
            continue
        for c in line:
            if c == "{":
                left_bracket += 1
            elif c == "}":
                left_bracket -= 1

        if left_bracket < 0:
            print(f"{filepath}:{i} left_bracket < 0")
            sys.exit(1)
        if left_bracket == 0:
            ret.append((begin, i + 1))

    return ret


def do(filepath):
    with open(filepath) as file:
        lines = [line.rstrip() for line in file.readlines()]
    bes = find_err_lines(filepath, lines)
    for begin, end in bes:
        if has_unconsumed_error(lines[begin:end]):
            print(f"{filepath}:{begin}")
            for line in lines[begin:end]:
                print(line)


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
