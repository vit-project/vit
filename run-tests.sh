#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly ROOT_DIR

cd "${ROOT_DIR}"
exec python -m pytest "${@}"
