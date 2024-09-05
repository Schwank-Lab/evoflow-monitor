## Maintenance 

To create a backup of the database run: 

```
poetry run python evoflow_db/db_backup.py
```

Note: this requires `pg_dump` command line tool, on linux can be installed using `sudo apt-get install postgresql-client`. 


To create all tables in the database run: 

```
poetry run python evoflow_db/db_create_tables.py
```