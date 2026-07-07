# Flask App

## Development

Endpoints to interact with the API are defined in `routes/`. Every endpoint must be routed in a `Blueprint` which is registered in `__init__.py`. Current practice is to intake the request payload in the route, validate it using Marshmallow and basic exists queries, then defer all handling to a corresponding function in `services/` and return the response using Marshmallow to serialize the service function output.

## Making Changes to Models

Whenever the `models.py` file is modified to add columns to tables, etc., you must **migrate** the database using Alembic. Alembic uses a Python abstraction to dispatch SQL commands that modify the tables. Modifying tables yourself in SQL is **not recommended** and will make your database out-of-sync with the repo.

The database can be migrated by running:

```bash
make MSG='Added column x to table y' migrate
make upgrade
```

These commands must be performed while the app is running. `make upgrade` is optional but will upgrade the database (apply the migrations) on the spot rather than waiting for the next restart (at which point they are automatically applied).

**Important note**: Running `migrate` does not perfectly generate a migration script. Often times, _especially_ with enum columns with PostgreSQL, manually editing of the generated script in `migrations/versions/` will be required. If you run into errors while running `upgrade`, you will likely need to edit the script (or delete conflicting data in the database).

### Updating Enum Columns

Alembic will frequently auto-generate incorrect scripts for updating enum columns (or not generate any). The expected format should be as follows:

```python
def upgrade():
    op.execute("ALTER TYPE enumnametype ADD VALUE 'VALUE3'")


def downgrade():
    # delete rows using the value
    op.execute("DELETE FROM tablename WHERE columnname = 'VALUE3'")

    # rename current enum type
    op.execute("ALTER TYPE enumnametype RENAME TO enumnametype_old")

    # recreate enum with old values
    op.execute(
        "CREATE TYPE enumnametype AS ENUM('VALUE1', 'VALUE2')"
    )

    # cast to new type
    op.execute(
        "ALTER TABLE tablename ALTER COLUMN columnname DROP DEFAULT,"  # if a default exists, often needs to be temporarily dropped
        "ALTER COLUMN columnname TYPE enumnametype USING columnname::text::enumnametype,"
        "ALTER COLUMN columnname SET DEFAULT 'VALUE1';"
    )

    # remove old enum type
    op.execute("DROP TYPE enumnametype_old")
```
