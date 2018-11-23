SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

export PYTHONPATH=$PYTHONPATH:$SCRIPTPATH/..
echo $PYTHONPATH

# General
export INFRABOX_GENERAL_REPORT_ISSUE_URL=https://github.com/SAP/infrabox/issues
export INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES=true

# DB Configuration
export INFRABOX_DATABASE_DB=postgres
export INFRABOX_DATABASE_PORT=5439
export INFRABOX_DATABASE_HOST=localhost
export INFRABOX_DATABASE_USER=postgres
export INFRABOX_DATABASE_PASSWORD=postgres

# Open Policy Agent (OPA)
export INFRABOX_OPA_HOST=localhost
export INFRABOX_OPA_PORT=8181
export INFRABOX_OPA_PUSH_INTERVAL=60

# Service Config
export INFRABOX_VERSION=local
export INFRABOX_LOG_LEVEL=debug
export INFRABOX_ROOT_URL=http://localhost:8080
export INFRABOX_CLUSTER_NAME=master

# S3 Config
export INFRABOX_STORAGE_GCS_ENABLED=false
export INFRABOX_STORAGE_S3_ENABLED=true
export INFRABOX_STORAGE_S3_SECURE=false
export INFRABOX_STORAGE_S3_REGION=us-east-1
export INFRABOX_STORAGE_S3_ENDPOINT=http://minio
export INFRABOX_STORAGE_S3_PORT=9000
export INFRABOX_STORAGE_S3_BUCKET=infrabox
export INFRABOX_STORAGE_S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
export INFRABOX_STORAGE_S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Azure
export INFRABOX_STORAGE_AZURE_ENABLED=false

# Swift
export INFRABOX_STORAGE_SWIFT_ENABLED=false


# Account
export INFRABOX_ACCOUNT_SIGNUP_ENABLED=true
export INFRABOX_ACCOUNT_LDAP_ENABLED=false
export INFRABOX_ACCOUNT_SAML_ENABLED=false

# Github
export INFRABOX_GITHUB_ENABLED=false
export INFRABOX_GITHUB_LOGIN_ENABLED=false

# Gerrit
export INFRABOX_GERRIT_ENABLED=false

# RSA
export INFRABOX_RSA_PRIVATE_KEY_PATH=../../infrabox/test/utils/id_rsa
export INFRABOX_RSA_PUBLIC_KEY_PATH=../../infrabox/test/utils/id_rsa.pub

#HA Mode
export INFRABOX_HA_ENABLED=false

#Legal
export INFRABOX_LEGAL_PRIVACY_URL=https://www.sap.com/about/legal/privacy.html
export INFRABOX_LEGAL_TERMS_OF_USE_URL=https://www.sap.com/corporate/en/legal/terms-of-use.html


python server.py
