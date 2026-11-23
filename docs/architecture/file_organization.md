# File Organization

## Description

This file contains the structure of the files in the project and file naming convention.

### Structure

PROJECT_ARCHIVIST/
├── archivist/
│   ├── config/
│   │   └── settings.py
│   │
│   ├── core/
│   │   ├── agent.py
│   │   ├── conversation.py
│   │   ├── exceptions.py
│   │   ├── harness.py
│   │   └── message.py
│   │
│   ├── interfaces/
│   │   ├── cli/
│   │   └── webui/
│   │
│   ├── llm_providers/
│   │   ├── llamacpp_server.py
│   │   ├── LLM_provider.py
│   │   └── serialize.py
│   │
│   └── storage/
│       └── SQLite.py
│
├── data/                       # runtime generated data
│   ├── agents/
│   │   └── CLaRA/              # main agent
│   └── conversations/
│   │   └── conversations.db
│
├── labs/                       # not yet implemented
│   ├── agent_loops/
│   └── prototypes/
│
├── tests/
├── ADRs/
├── pyproject.toml
└── README.md