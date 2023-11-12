# Data analysis from [kiva.org](https://www.kiva.org)

## Environment setup

```bash
pip install -r requirements/dev-requirements.txt requirements/requirements.txt
# OR
pip-sync requirements/dev-requirements.txt requirements/requirements.txt
```

## Usage

Fetch the data with

```bash
python src/fetch_loans.py -f data/first_run
```

## developer notes

- please use `pre-commit`. Just lauch `pre-commit install`
- generate `schema.graphql` from introspection with

  ```bash
  gql-cli --print-schema 'https://api.kivaws.org/graphql' >! schema.graphql
  ```

- generate `pydantic` from introspection with

  ```bash
  python -m gql_schema_codegen -u https://api.kivaws.org/graphql -t ./schema_types.py
  ```

- avoid commit huge notebook with

  ```bash
  nbstripout --install --attributes .gitattributes
  ```

## Visualize the graphql

```bash
npm install -g get-graphql-schema
get-graphql-schema 'https://api.kivaws.org/graphql' > schema2.graphql         
```

Copy the content of `schema2.graphql` and paste into <https://graphql-kit.com/graphql-voyager/>


## `cuDF`

```bash
conda create --solver=libmamba -n cudf -c rapidsai -c conda-forge -c nvidia rapids=23.08 python=3.10 cudatoolkit=11.8 graphviz cugraph
```

## Generate report

```bash
jupyter nbconvert --to html alldata_cudf.ipynb
```

## best practice with jupter notebook

ref: https://blog.jmswaney.com/tips-for-using-jupyter-notebooks-with-github
