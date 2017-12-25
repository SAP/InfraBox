#!/bin/sh -e
git clone https://github.com/InfraBox/cli.git /cli
cd /cli
pip install -e .

python /infrabox/context/infrabox/test/e2e-compose/test.py
