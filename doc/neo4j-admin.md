# `neo4j-admin` usage to upload data

First, run with

```bash
cd extra
docker compose exec neo4j /bin/bash
```


```bash
neo4j-admin database import full --nodes=/downloads/tags.csv --nodes=/downloads/loans.csv --nodes=/downloads/lenders.csv  --relationships=/downloads/loan_tags.csv --relationships=/downloads/lender_loan.csv testdb
```

Since we're working with community

> The Community Edition of Neo4j supports running a single database at a time

Then we've have to apply hacked into the conf file

```bash
sed -i -e '$ainitial.dbms.default_database=testdb' conf/neo4j.conf 
```


Then restart the docker
```bash
docker compose restart
docker compose logs
```

Now navigate to `http://localhost:7474` and `:use testdb` to start.