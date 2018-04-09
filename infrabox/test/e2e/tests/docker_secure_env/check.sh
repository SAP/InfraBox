#!/bin/sh -e
if [ "$ENV_VAR_1" = "hello world" ]; then
    echo "correct"
    exit 0
else
    echo "wrong"
    exit 1
fi

