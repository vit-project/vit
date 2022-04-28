#!/usr/bin/env bash

pids="$(vit --list-pids)"
for pid in ${pids}; do
  kill -SIGUSR1 ${pid} &>/dev/null
done
