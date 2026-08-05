-- Run via db-init.sh, not directly — needs psql variables set from .env

CREATE ROLE ag_abfrage_svc LOGIN PASSWORD :'AG_ABFRAGE_PASSWORD';

GRANT CONNECT ON DATABASE cartei TO ag_abfrage_svc;
GRANT SELECT, INSERT, UPDATE ON ag_abfrage, ag_abfrage_result TO ag_abfrage_svc;
GRANT SELECT, INSERT ON entity_history TO ag_abfrage_svc;

-- Only expose the tenant FK target column; no financial/personal data
GRANT SELECT (id, intranet_username, intranet_uuid) ON tenant TO ag_abfrage_svc;
