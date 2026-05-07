# File Organization

## Description

This file contains the structure of the files in the project and file naming convention.

### Structure

PROJECT_ARCHIVIST/
├── archivist/
│   ├── core/
│   │   ├── orchestrator.py
│   │   ├── planner.py
│   │   ├── router.py
│   │   └── context.py
│   │
│   ├── agents/
│   ├── tools/
│   ├── memory/
│   │   ├── store.py
│   │   ├── embeddings.py
│   │   └── vector_index.py
│   │
│   ├── models/
│   ├── webui/
│   └── utils/
│
├── data/                     # ALL runtime state
│   ├── agents/
│   ├── conversations/
│   ├── memory/
│   ├── vectors/
│   └── caches/
│
├── labs/
│   ├── agent_loops/
│   └── prototypes/
│
├── tests/
├── ADRs/
├── pyproject.toml
└── README.md