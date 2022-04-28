#!/usr/bin/env bash

# Auto-refreshes all open VIT interfaces on any modifications.
# Looks for the special $IS_VIT_INSTANCE environment variable,
# and if found, skips the refresh.

# Make sure this script is in your PATH and executable, modify as necessary.
# Refer to the example at scripts/vit-external-refresh.sh
REFRESH_SCRIPT="vit-external-refresh.sh"

# Count the number of tasks modified
n=0
while read modified_task; do
    n=$((${n} + 1))
done

if ((${n} > 0)); then
  if [ -z "${IS_VIT_INSTANCE}" ]; then
    logger "Tasks modified outside of VIT: ${n}, refreshing"
    ${REFRESH_SCRIPT}
  fi
fi

exit 0
