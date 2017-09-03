#!/bin/bash

helm delete --purge infrabox
helm delete --purge infrabox-postgres
helm delete --purge infrabox-minio

kubectl delete secret -n infrabox-worker infrabox-docker-registry

kubectl delete secret -n infrabox-system infrabox-dashboard
kubectl delete secret -n infrabox-system infrabox-docker-registry
kubectl delete secret -n infrabox-system infrabox-github
kubectl delete secret -n infrabox-system infrabox-s3-credentials
