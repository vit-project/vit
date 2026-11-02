#!/usr/bin/env bash

set -euo pipefail

build_release() {
  local release_dir
  echo "Installing build and release dependencies from pyproject.toml"
  python -m pip install --upgrade --group release
  mkdir -p dist
  release_dir="$(mktemp -d dist/release.XXXXXX)"
  echo "Building distributions in ${release_dir}"
  python -m build --outdir "${release_dir}"
  echo "Checking built distributions"
  python -m twine check --strict "${release_dir}"/*
  echo "Build successful and verified"
  echo
  echo "Test release with command:"
  echo "  python -m twine upload --repository testpypi ${release_dir}/*"
  echo
  echo "Release with command:"
  echo "  python -m twine upload --skip-existing ${release_dir}/*"
}

if [[ ! -d vit || ! -r pyproject.toml ]]; then
  echo "ERROR: must run script from VIT repository root" >&2
  exit 1
fi

build_release
