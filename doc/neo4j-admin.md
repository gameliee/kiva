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


## Post import

```cypher
CREATE CONSTRAINT FOR (lender:Lender)
REQUIRE lender.id IS UNIQUE
```

```cypher
CREATE CONSTRAINT FOR (tag:Tag)
REQUIRE tag.name IS UNIQUE
```

```cypher
CREATE CONSTRAINT FOR (loan:Loan)
REQUIRE loan.id IS UNIQUE
```

### stats

```cypher
MATCH () RETURN COUNT(*) AS STATS
UNION
MATCH ()-[]->() RETURN COUNT(*) AS STATS
```

╒════════╕
│STATS   │
╞════════╡
│4035815 │
├────────┤
│55563775│
└────────┘

### create `INTEREST` relationships


```cypher
CALL apoc.periodic.iterate(
"MATCH (lender:Lender) RETURN lender",
"MATCH (lender)-[:LEND]->(loan:Loan)
 WITH DISTINCT loan as dloan, lender
 MATCH (dloan)-[:TAGGED_WITH]->(tag:Tag)
 WITH DISTINCT tag as dtag, lender
 CREATE (lender)-[:INTEREST]->(dtag)",
{batchSize: 100, parallel: True}
)
```

╒════════╕
│STATS   │
╞════════╡
│4035815 │
├────────┤
│69135480│
└────────┘


### create `SHARES_LOAN` relationships

```cypher
CALL apoc.periodic.iterate(
"MATCH (l1:Lender), (l2:Lender)
 WHERE elementId(l1) > elementId(l2)
 RETURN l1, l2",
"MATCH (l1)-[:LEND]->(loan)<-[:LEND]-(l2)
 WITH l1, l2, COUNT(DISTINCT loan) AS commonLoanCount
 WHERE commonLoanCount > 0
 CREATE (l1)-[r:SHARES_LOAN {weight: commonLoanCount}]->(l2)",
{batchSize: 100, parallel: True}
)
YIELD *
```


