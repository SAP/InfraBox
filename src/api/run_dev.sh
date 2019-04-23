#!/bin/bash -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

watch=$DIR/..
echo "Watching: $watch"

sigint_handler()
{
    kill $PID
    exit
}

trap sigint_handler SIGINT

while true; do
    python $DIR/server.py &
    PID=$!
    inotifywait -e modify -e move -e create --exclude='.*__pycache__.*' -r $watch
    kill $PID
done
