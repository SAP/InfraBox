{{- define "system_namespace" -}}
{{- required "system_namespace is required" .Values.system_namespace -}}
{{- end -}}

{{- define "worker_namespace" -}}
{{- required "worker_namespace is required" .Values.worker_namespace -}}
{{- end -}}

{{- define "root_url" -}}
{{- if eq 443.0 .Values.port -}}
https://{{- required "host is required" .Values.host -}}
{{- else -}}
https://{{- required "host is required" .Values.host -}}:{{- .Values.port -}}
{{- end -}}
{{- end -}}

{{- define "image_repository" -}}
{{- required "image.repository is required" .Values.image.repository -}}
{{- end -}}

{{- define "image_tag" -}}
{{- required "image.tag is required" .Values.image.tag -}}
{{- end -}}

{{ define "env_database" }}
-
    name: INFRABOX_DATABASE_USER
    valueFrom:
        secretKeyRef:
            name: infrabox-postgres
            key: username
-
    name: INFRABOX_DATABASE_PASSWORD
    valueFrom:
        secretKeyRef:
            name: infrabox-postgres
            key: password
{{ if .Values.database.postgres.enabled }}
-
    name: INFRABOX_DATABASE_HOST
    value: {{ required "database.postgres.host is required" .Values.database.postgres.host | quote }}
-
    name: INFRABOX_DATABASE_DB
    value: {{ required "database.postgres.db is required" .Values.database.postgres.db | quote }}
-
    name: INFRABOX_DATABASE_PORT
    value: {{ required "database.postgres.port is required" .Values.database.postgres.port | quote }}
{{ end }}
{{ if .Values.database.cloudsql.enabled }}
-
    name: INFRABOX_DATABASE_HOST
    value: localhost
-
    name: INFRABOX_DATABASE_DB
    value: {{ required "database.cloudsql.db is required" .Values.database.cloudsql.db | quote }}
-
    name: INFRABOX_DATABASE_PORT
    value: "5432"
-
    name: INFRABOX_STORAGE_CLOUDSQL_INSTANCE_CONNECTION_NAME
    value: {{ .Values.database.cloudsql.instance_connection_name }}
{{ end }}
{{ end }}

{{ define "volumes_rsa" }}
-
    name: rsa-key
    secret:
        secretName: infrabox-rsa
{{ end }}

{{ define "mounts_rsa_private" }}
-
    name: rsa-key
    mountPath: "/var/run/secrets/infrabox.net/rsa/id_rsa"
    subPath: id_rsa
    readOnly: true
{{ end }}

{{ define "mounts_rsa_public" }}
-
    name: rsa-key
    mountPath: "/var/run/secrets/infrabox.net/rsa/id_rsa.pub"
    subPath: id_rsa.pub
    readOnly: true
{{ end }}

{{ define "mounts_gcs" }}
{{ if .Values.storage.gcs.enabled }}
-
    name: gcs-service-account
    mountPath: /etc/infrabox/gcs
    readOnly: true
{{ end }}
{{ end }}

{{ define "mounts_gerrit" }}
{{ if .Values.gerrit.enabled }}
-
    name: gerrit-ssh
    mountPath: /tmp/gerrit
    readOnly: true
{{ end }}
{{ end }}

{{ define "volumes_gerrit" }}
{{ if .Values.gerrit.enabled }}
-
    name: gerrit-ssh
    secret:
        secretName: infrabox-gerrit-ssh
{{ end }}
{{ end }}

{{ define "volumes_gcs" }}
{{ if .Values.storage.gcs.enabled }}
-
    name: gcs-service-account
    secret:
        secretName: infrabox-gcs
{{ end }}
{{ end }}

{{ define "volumes_database" }}
{{ if .Values.database.cloudsql.enabled }}
-
    name: cloudsql-instance-credentials
    secret:
        secretName: infrabox-cloudsql-instance-credentials
-
    name: cloudsql
    emptyDir:
{{ end }}
{{ end }}

{{ define "env_account" }}
-
    name: INFRABOX_ACCOUNT_SIGNUP_ENABLED
    value: {{ .Values.account.signup.enabled | quote }}
{{ end }}

{{ define "env_gcs" }}
-
    name: INFRABOX_STORAGE_GCS_ENABLED
    value: {{ .Values.storage.gcs.enabled | quote }}
{{ if .Values.storage.gcs.enabled }}
-
    name: INFRABOX_STORAGE_GCS_BUCKET
    value: {{ .Values.storage.gcs.bucket }}
-
    name: GOOGLE_APPLICATION_CREDENTIALS
    value: /etc/infrabox/gcs/gcs_service_account.json
{{ end }}
{{ end }}

{{ define "env_s3" }}
-
    name: INFRABOX_STORAGE_S3_ENABLED
    value: {{ .Values.storage.s3.enabled | quote }}
{{ if .Values.storage.s3.enabled }}
-
    name: INFRABOX_STORAGE_S3_ENDPOINT
    value: {{ .Values.storage.s3.endpoint }}
-
    name: INFRABOX_STORAGE_S3_PORT
    value: {{ .Values.storage.s3.port | quote }}
-
    name: INFRABOX_STORAGE_S3_REGION
    value: {{ .Values.storage.s3.region | quote }}
-
    name: INFRABOX_STORAGE_S3_SECURE
    value: {{ .Values.storage.s3.secure | quote }}
-
    name: INFRABOX_STORAGE_S3_BUCKET
    value: {{ default "infrabox" .Values.storage.s3.bucket | quote }}
-
    name: INFRABOX_STORAGE_S3_ACCESS_KEY
    valueFrom:
        secretKeyRef:
            name: infrabox-s3-credentials
            key: accessKey
-
    name: INFRABOX_STORAGE_S3_SECRET_KEY
    valueFrom:
        secretKeyRef:
            name: infrabox-s3-credentials
            key: secretKey
{{ end }}
{{ end }}

{{ define "env_azure" }}
-
    name: INFRABOX_STORAGE_AZURE_ENABLED
    value: {{ .Values.storage.azure.enabled | quote }}
{{ if .Values.storage.azure.enabled }}
-
    name: INFRABOX_STORAGE_AZURE_ACCOUNT_NAME
    valueFrom:
        secretKeyRef:
            name: infrabox-azure-credentials
            key: account-name
-
    name: INFRABOX_STORAGE_AZURE_ACCOUNT_KEY
    valueFrom:
        secretKeyRef:
            name: infrabox-azure-credentials
            key: account-key
{{ end }}
{{ end }}

{{ define "env_swift" }}
-
    name: INFRABOX_STORAGE_SWIFT_ENABLED
    value: {{ .Values.storage.swift.enabled | quote }}
{{ if .Values.storage.swift.enabled }}
-
    name: INFRABOX_STORAGE_SWIFT_PROJECT_NAME
    value: {{ .Values.storage.swift.project_name }}
-
    name: INFRABOX_STORAGE_SWIFT_PROJECT_DOMAIN_NAME
    value: {{ .Values.storage.swift.project_domain_name }}
-
    name: INFRABOX_STORAGE_SWIFT_USER_DOMAIN_NAME
    value: {{ .Values.storage.swift.user_domain_name }}
-
    name: INFRABOX_STORAGE_SWIFT_AUTH_URL
    value: {{ .Values.storage.swift.auth_url }}
-
    name: INFRABOX_STORAGE_SWIFT_CONTAINER_NAME
    value: {{ .Values.storage.swift.container_name }}
-
    name: INFRABOX_STORAGE_SWIFT_USERNAME
    valueFrom:
        secretKeyRef:
            name: infrabox-swift-credentials
            key: username
-
    name: INFRABOX_STORAGE_SWIFT_PASSWORD
    valueFrom:
        secretKeyRef:
            name: infrabox-swift-credentials
            key: password
{{ end }}
{{ end }}

{{ define "env_github" }}
-
    name: INFRABOX_GITHUB_ENABLED
    value: {{ .Values.github.enabled | quote }}
{{ if .Values.github.enabled }}
-
    name: INFRABOX_GITHUB_LOGIN_ENABLED
    value: {{ .Values.github.login.enabled | quote }}
-
    name: INFRABOX_GITHUB_API_URL
    value: {{ default "https://api.github.com" .Values.github.api_url }}
-
    name: INFRABOX_GITHUB_LOGIN_URL
    value: {{ default "https://github.com/login" .Values.github.login.url }}
-
    name: INFRABOX_GITHUB_LOGIN_ALLOWED_ORGANIZATIONS
    value: {{ default "" .Values.github.login.allowed_organizations | quote }}
{{ end }}
{{ end }}

{{ define "env_gerrit" }}
-
    name: INFRABOX_GERRIT_ENABLED
    value: {{ .Values.gerrit.enabled | quote }}
{{ if .Values.gerrit.enabled }}
-
    name: INFRABOX_GERRIT_HOSTNAME
    value: {{ required "gerrit.hostname is required" .Values.gerrit.hostname }}
-
    name: INFRABOX_GERRIT_KEY_FILENAME
    value: /home/infrabox/.ssh/id_rsa
-
    name: INFRABOX_GERRIT_USERNAME
    value: {{ required "gerrit.username is required" .Values.gerrit.username }}
-
    name: INFRABOX_GERRIT_PORT
    value: {{ default "29418" .Values.gerrit.port | quote }}
{{ end }}
{{ end }}

{{ define "env_ldap" }}
-
    name: INFRABOX_ACCOUNT_LDAP_ENABLED
    value: {{ .Values.account.ldap.enabled | quote }}
{{ if .Values.account.ldap.enabled }}
-
    name: INFRABOX_ACCOUNT_LDAP_URL
    value: {{ required "account.ldap.url is required" .Values.account.ldap.url }}
-
    name: INFRABOX_ACCOUNT_LDAP_BASE
    value: {{ required "account.ldap.base is required" .Values.account.ldap.base }}
-
    name: INFRABOX_ACCOUNT_LDAP_DN
    valueFrom:
        secretKeyRef:
            name: infrabox-ldap
            key: dn
-
    name: INFRABOX_ACCOUNT_LDAP_PASSWORD
    valueFrom:
        secretKeyRef:
            name: infrabox-ldap
            key: password
{{ end }}
{{ end }}

{{ define "env_saml" }}
-
    name: INFRABOX_ACCOUNT_SAML_ENABLED
    value: {{ .Values.account.saml.enabled | quote }}
{{ if .Values.account.saml.enabled }}
-
    name: INFRABOX_ACCOUNT_SAML_NAME_FORMAT
    value: {{ .Values.account.saml.format.name | quote }}
-
    name: INFRABOX_ACCOUNT_SAML_USERNAME_FORMAT
    value: {{ .Values.account.saml.format.username | quote }}
-
    name: INFRABOX_ACCOUNT_SAML_EMAIL_FORMAT
    value: {{ .Values.account.saml.format.email | quote }}
-
    name: INFRABOX_ACCOUNT_SAML_SETTINGS_PATH
    value: "/var/run/secrets/infrabox.net/saml"
{{ end }}
{{ end }}

{{ define "mounts_saml" }}
{{ if .Values.account.saml.enabled }}
-
    name: saml
    mountPath: "/var/run/secrets/infrabox.net/saml"
    readOnly: true
{{ end }}
{{ end }}

{{ define "volumes_saml" }}
{{ if .Values.account.saml.enabled }}
-
    name: saml
    configMap:
        name: infrabox-saml
{{ end }}
{{ end }}


{{ define "env_legal" }}
-
    name: INFRABOX_LEGAL_PRIVACY_URL
    value: {{ .Values.legal.privacy_url }}
-
    name: INFRABOX_LEGAL_TERMS_OF_USE_URL
    value: {{ .Values.legal.terms_of_use_url }}

{{ end }}

{{ define "env_github_secrets" }}
{{ if .Values.github.enabled }}
-
    name: INFRABOX_GITHUB_CLIENT_ID
    valueFrom:
        secretKeyRef:
            name: infrabox-github
            key: client_id
-
    name: INFRABOX_GITHUB_CLIENT_SECRET
    valueFrom:
        secretKeyRef:
            name: infrabox-github
            key: client_secret
-
    name: INFRABOX_GITHUB_WEBHOOK_SECRET
    valueFrom:
        secretKeyRef:
            name: infrabox-github
            key: webhook_secret
{{ end }}
{{ end }}

{{ define "env_version" }}
-
    name: INFRABOX_VERSION
    value: {{ include "image_tag" . }}
{{ end }}

{{ define "github_access" }}
-
    name: INFRABOX_GITHUB_ENABLED
    value: {{ .Values.github.enabled | quote }}
{{- if .Values.github.enabled }}
-
    name: GITHUB_HOST
    value: {{ .Values.github.host }}
-
    name: GITHUB_ENABLE_TOKEN_ACCESS
    value: {{ .Values.github.token_access | quote}}
{{ end }}
{{ end }}

{{ define "env_cluster" }}
-
    name: INFRABOX_CLUSTER_NAME
    value: {{ required "cluster.name is required" .Values.cluster.name }}
-
    name: INFRABOX_CLUSTER_LABELS
    value: {{ .Values.cluster.labels }}
{{ end }}

{{ define "env_opa" }}
-
    name: INFRABOX_OPA_HOST
    value: localhost
-
    name: INFRABOX_OPA_PORT
    value: "8181"
-
    name: INFRABOX_OPA_PUSH_INTERVAL
    value: "30"
{{ end }}

{{ define "env_general" }}
-
    name: INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES
    value: {{ default "false" .Values.general.dont_check_certificates | quote }}
-
    name: INFRABOX_DEV
    value: {{ .Values.dev.enabled | quote }}
-
    name: INFRABOX_GENERAL_WORKER_NAMESPACE
    value: {{ template "worker_namespace" . }}
-
    name: INFRABOX_GENERAL_SYSTEM_NAMESPACE
    value: {{ template "system_namespace" . }}
-
    name: INFRABOX_ROOT_URL
    value: {{ template "root_url" . }}
-
    name: INFRABOX_VERSION
    value: {{ template "image_tag" . }}
-
    name: INFRABOX_GENERAL_REPORT_ISSUE_URL
    value: {{ .Values.general.report_issue_url }}
-
    name: INFRABOX_LOG_LEVEL
    value: {{ .Values.general.log_level }}
{{ end }}

{{ define "env_docker_registry" }}
-
    name: INFRABOX_DOCKER_REGISTRY_ADMIN_USERNAME
    value: "admin"
-
    name: INFRABOX_DOCKER_REGISTRY_ADMIN_PASSWORD
    valueFrom:
        secretKeyRef:
            name: infrabox-admin
            key: password
{{ end }}

{{ define "containers_database" }}
{{ if .Values.database.cloudsql.enabled }}
-
    image: gcr.io/cloudsql-docker/gce-proxy:1.09
    name: cloudsql-proxy
    command: ["/cloud_sql_proxy", "--dir=/cloudsql",
              "-instances={{ .Values.database.cloudsql.instance_connection_name }}=tcp:5432",
              "-credential_file=/secrets/cloudsql/credentials.json"]
    volumeMounts:
    - name: cloudsql-instance-credentials
      mountPath: /secrets/cloudsql
      readOnly: true
    - name: cloudsql
      mountPath: /cloudsql
{{ end }}
{{ end }}

{{ define "containers_opa" }}
-
    image: {{ include "image_repository" . }}/opa:{{ include "image_tag" . }}
    name: opa
{{ end }}

{{- define "dockerCredentials" }}
{{- printf "{\"auths\": {\"%s\": {\"auth\": \"%s\"}}}" .Values.image.repository (printf "%s:%s" .Values.image.username .Values.image.password | b64enc) | b64enc }}
{{- end }}

{{ define "imagePullSecret" }}
{{ if .Values.image.private_repo }}
    imagePullSecrets:
    - name: infrabox-docker-credentials
{{ end }}
{{ end }}

{{- define "ha_global_url" -}}
{{- if eq 443.0 .Values.ha.global_port -}}
https://{{- .Values.ha.global_host -}}
{{- else -}}
https://{{- .Values.ha.global_host -}}:{{- .Values.ha.global_port -}}
{{- end -}}
{{- end -}}

{{ define "env_ha" }}
-   name: INFRABOX_HA_ENABLED
    value: {{ .Values.ha.enabled | quote }}
{{ if or .Values.ha.enabled .Values.monitoring.enabled  }}
-   name: INFRABOX_HA_CHECK_INTERVAL
    value: {{ .Values.ha.check_interval | quote }}
-   name: INFRABOX_HA_ACTIVE_TIMEOUT
    value: {{ .Values.ha.active_timeout | quote }}
-   name: INFRABOX_HA_GLOBAL_URL
    value: {{ template "ha_global_url" . }}
{{ end }}
{{ end }}

{{ define "env_monitoring" }}
-   name: INFRABOX_MONITORING_ENABLED
    value: {{ .Values.monitoring.enabled | quote }}
{{ end }}

{{ define "env_cachet" }}
-
    name: INFRABOX_CACHET_ENABLED
    value: {{ .Values.cachet.enabled | quote }}
-   name: INFRABOX_CACHET_API_TOKEN
    value: {{ .Values.cachet.api_token }}
-   name: INFRABOX_CACHET_ENDPOINT
    value: {{ .Values.cachet.endpoint | quote }}
{{ end }}

{{ define "volumes_dev" }}
{{ if .Values.dev.enabled }}
-
    name: code
    hostPath:
        path: {{ .Values.dev.repo_path }}
{{ end }}
{{ end }}