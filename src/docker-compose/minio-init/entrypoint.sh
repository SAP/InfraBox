#!/bin/sh

sleep 10
mc config host add compose http://minio:9000 AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

until mc ls compose &> /dev/null; do
    echo "minio not yet ready"
    sleep 1
done

mc mb compose/infrabox-container-content-cache
mc mb compose/infrabox-project-upload
mc mb compose/infrabox-container-output
mc mb compose/infrabox-docker-registry

while true
do
    sleep 1
done
