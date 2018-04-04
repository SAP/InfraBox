#!/bin/sh
set -e

host=$1
shift
cmd="$@"

until $(curl --output /dev/null --silent --head --fail http://$host/ping); do
  sleep 1
done

$cmd
