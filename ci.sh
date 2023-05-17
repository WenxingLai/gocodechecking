#!/usr/bin/env bash
cd "$1" || exit 1
golangci-lint run -E makezero -E exportloopref -E nilerr -E nilnil -E wastedassign
staticcheck -tests=false -checks 'all,-S1002,-SA1019,-ST1000,-ST1003,-ST1005,-ST1012,-ST1016,-ST1020,-ST1021,-ST1022,-U1000,-ST1008' ./...
