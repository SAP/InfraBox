#!/bin/bash
compose_file=$1
docker-compose -f $compose_file ps -q | xargs docker inspect -f '{{ .State.ExitCode }}' | while read code; do  
    if [ "$code" == "1" ]; then    
       exit -1
    fi
done  
