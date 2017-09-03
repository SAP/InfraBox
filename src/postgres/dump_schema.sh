host=$1
port=$2

pg_dump -h $host -p $port -U postgres test_db --schema-only --create -O | sed 's/infrabox/test_db/' > schema_testing.sql
dos2unix schema_testing.sql

pg_dump -h $host -p $port -U postgres test_db --schema-only --create -O | sed 's/test_db/infrabox/' > schema_production.sql
dos2unix schema_production.sql
