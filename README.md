# Data analysis from [kiva.org](https://www.kiva.org)

## Usage

Fetch the data with

```bash
python src/fetch_loans.py -f data/first_run
```

## developer notes

- please use `pre-commit`
- generate `schema.graphql` from introspection with

  ```bash
  gql-cli --print-schema 'https://api.kivaws.org/graphql' >! schema.graphql
  ```

- generate `pydantic` from introspection with

  ```bash
  python -m gql_schema_codegen -u https://api.kivaws.org/graphql -t ./schema_types.py
  ```

## Visualize the graphql

```bash
npm install -g get-graphql-schema
get-graphql-schema 'https://api.kivaws.org/graphql' > schema2.graphql         
```

Copy the content of `schema2.graphql` and paste into <https://graphql-kit.com/graphql-voyager/>
