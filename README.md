# Data analysis from [kiva.org](https://www.kiva.org)

This project contains scripts and notebooks for

- Download data from the kiva platform
- Data preprocessing (simple ELT)
- Various analysis on the data

Project tree:

```text
.
├── data
│   ├── gen: for store graphs, including Nodes, Edges, etc.
├── doc: random notes go here
├── extra: for setup experiment tools: memgraph, postgres,
├── fulldata: raw data files go here
└── src: source files go here
    ├── checkpoints: store intermediate files
    ├── images: store intermediate images
```

## Environment setup

```bash
# macos
pip-sync requirements/mac-requirements.txt requirements/requirements.txt
# linux
pip-sync requirements/requirements.txt
```

