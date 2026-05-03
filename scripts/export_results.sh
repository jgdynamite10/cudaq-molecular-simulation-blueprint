#!/usr/bin/env bash
# Snapshot the results/ directory into a tarball for archiving + blog.
set -euo pipefail

ts="$(date -u +%Y%m%dT%H%M%SZ)"
out="results-${ts}.tar.gz"
tar -czf "${out}" results/
echo "wrote ${out}"
