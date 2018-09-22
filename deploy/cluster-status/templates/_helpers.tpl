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
