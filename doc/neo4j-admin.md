# `neo4j-admin` usage to upload data

First, run with

```bash
cd extra
docker compose up -d
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

╒═══════╕
│STATS  │
╞═══════╡
│736303 │
├───────┤
│7876267│
└───────┘

remove all Nodes which doesn't have any relationship

```cypher
MATCH (n)
WHERE NOT (n)--()
DELETE (n)
```

Easy out

```cypher
MATCH (loan:Loan)
WHERE loan.fundraisingDate < '2018-01-01'
RETURN COUNT(loan)
UNION
MATCH (loan:Loan)
RETURN COUNT(loan)
```

╒═══════════╕
│COUNT(loan)│
╞═══════════╡
│1150133    │
├───────────┤
│2092121    │
└───────────┘

With 2 milions Loan, it could take forever to analysize the graph. So, keep only loans in latest 5 years

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
"MATCH (l1)-[:LEND]->(loan:Loan)<-[:LEND]-(l2)
 WITH l1, l2, COUNT(DISTINCT loan) AS commonLoanCount
 WHERE commonLoanCount > 0
 CREATE (l1)-[r:SHARES_LOAN {weight: commonLoanCount}]->(l2)",
{batchSize: 100, parallel: True}
)
YIELD *
```

### create `SHARES_TAG` relationships

```cypher
CALL apoc.periodic.iterate(
"MATCH (l1:Lender), (l2:Lender)
 WHERE elementId(l1) > elementId(l2)
 RETURN l1, l2",
"MATCH (l1)-[:INTEREST]->(tag:Tag)<-[:LEINTERESTND]-(l2)
 WITH l1, l2, COUNT(DISTINCT tag) AS commonTagCount
 WHERE commonTagCount > 0
 CREATE (l1)-[r:SHARES_TAG {weight: commonTagCount}]->(l2)",
{batchSize: 100, parallel: True}
)
YIELD *
```