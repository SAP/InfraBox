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
-
    name: INFRABOX_DATABASE_HOST
    value: {{ default "localhost" .Values.storage.postgres.host | quote }}
-
    name: INFRABOX_DATABASE_DB
    value: {{ default "infrabox" .Values.storage.postgres.db | quote }}
-
    name: INFRABOX_DATABASE_PORT
    value: {{ default 5432 .Values.storage.postgres.port | quote }}
-
    name: INFRABOX_STORAGE_CLOUDSQL_ENABLED
    value: {{ .Values.storage.cloudsql.enabled | quote }}
{{ if .Values.storage.cloudsql.enabled }}
-
    name: INFRABOX_STORAGE_CLOUDSQL_INSTANCE_CONNECTION_NAME
    value: {{ .Values.storage.cloudsql.instance_connection_name }}
{{ end }}
{{ end }}

{{ define "volumes_database" }}
{{ if .Values.storage.cloudsql.enabled }}
-
    name: cloudsql-instance-credentials
    secret:
        secretName: infrabox-cloudsql-instance-credentials
-
    name: ssl-certs
    hostPath:
        path: /etc/ssl/certs
-
    name: cloudsql
    emptyDir:
{{ end }}
{{ end }}

{{ define "env_gcs" }}
-
    name: INFRABOX_STORAGE_GCS_ENABLED
    value: {{ .Values.storage.gcs.enabled | quote }}
{{ if .Values.storage.gcs.enabled }}
-
    name: INFRABOX_STORAGE_GCS_PROJECT_ID
    value: {{ .Values.storage.gcs.project_id }}
-
    name: INFRABOX_STORAGE_GCS_CONTAINER_OUTPUT_BUCKET
    value: {{ .Values.storage.gcs.container_output_bucket }}
-
    name: INFRABOX_STORAGE_GCS_PROJECT_UPLOAD_BUCKET
    value: {{ .Values.storage.gcs.project_upload_bucket }}
-
    name: INFRABOX_STORAGE_GCS_CONTAINER_CONTENT_CACHE_BUCKET
    value: {{ .Values.storage.gcs.container_content_cache_bucket }}
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
    name: INFRABOX_STORAGE_S3_CONTAINER_OUTPUT_BUCKET
    value: {{ default "infrabox-container-output" .Values.storage.s3.container_output_bucket | quote }}
-
    name: INFRABOX_STORAGE_S3_PROJECT_UPLOAD_BUCKET
    value: {{ default "infrabox-project-upload" .Values.storage.s3.project_upload_bucket | quote }}
-
    name: INFRABOX_STORAGE_S3_CONTAINER_CONTENT_CACHE_BUCKET
    value: {{ default "infrabox-container-content-cache" .Values.storage.s3.container_content_cache_bucket | quote }}
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
    value: /root/.ssh/id_rsa
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

{{ define "env_general" }}
-
    name: INFRABOX_GENERAL_LOG_STACKDRIVER
    value: {{ default "false" .Values.general.log.stackdriver | quote }}
{{ end }}


{{ define "env_docker_registry" }}
-
    name: INFRABOX_DOCKER_REGISTRY_ADMIN_USERNAME
    valueFrom:
        secretKeyRef:
            name: infrabox-docker-registry
            key: username
-
    name: INFRABOX_DOCKER_REGISTRY_ADMIN_PASSWORD
    valueFrom:
        secretKeyRef:
            name: infrabox-docker-registry
            key: password
{{ end }}

{{ define "containers_database" }}
{{ if .Values.storage.cloudsql.enabled }}
-
    image: gcr.io/cloudsql-docker/gce-proxy:1.09
    name: cloudsql-proxy
    command: ["/cloud_sql_proxy", "--dir=/cloudsql",
              "-instances={{ .Values.storage.cloudsql.instance_connection_name }}=tcp:5432",
              "-credential_file=/secrets/cloudsql/credentials.json"]
    volumeMounts:
    - name: cloudsql-instance-credentials
      mountPath: /secrets/cloudsql
      readOnly: true
    - name: ssl-certs
      mountPath: /etc/ssl/certs
    - name: cloudsql
      mountPath: /cloudsql
{{ end }}
{{ end }}

{{ define "env_local_cache" }}
-
    name: INFRABOX_LOCAL_CACHE_ENABLED
    value: {{ .Values.local_cache.enabled | quote }}
{{ if .Values.local_cache.enabled }}
-
    name: INFRABOX_LOCAL_CACHE_HOST_PATH
    value: {{ default "/tmp/infrabox/local_cache" .Values.local_cache.host_path }}
{{ end }}
{{ end }}

{{ define "env_job" }}
-
    name: INFRABOX_JOB_MAX_OUTPUT_SIZE
    value: {{ default "104857600" .Values.job.max_output_size | quote }}
-
    name: INFRABOX_JOB_MOUNT_DOCKER_SOCKET
    value: {{ default "false" .Values.job.mount_docker_socket | quote }}
-
    name: INFRABOX_JOB_USE_HOST_DOCKER_DAEMON
    value: {{ default "false" .Values.job.use_host_docker_daemon | quote }}
{{ end }}

{{ define "env_kubernetes" }}
-
    name: INFRABOX_KUBERNETES_MASTER_HOST
    value: {{ default "kubernetes.default.svc.cluster.local" .Values.general.kubernetes_master_host }}
-
    name: INFRABOX_KUBERNETES_MASTER_PORT
    value: {{ default 443 .Values.general.kubernetes_master_port | quote }}
{{ end }}
