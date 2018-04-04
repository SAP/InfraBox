# Deploy Postgres
To install a PostgreSQL database in kubernetes simply run:

    helm install -n postgres --namespace infrabox-system --set postgresPassword=qweasdzxc1,postgresUser=infrabox,postgresDatabase=infrabox stable/postgresql

**This is not meant for production**

When configuring the InfraBox installation with `install.py` use these options:

    --database postgres
    --postgres-host postgres-postgresql.infrabox-system
    --postgres-username infrabox
    --postgres-database infrabox
    --postgres-port 5432
    --postgres-password qweasdzxc1

