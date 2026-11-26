# Project Archivist

Project name to be determined.  
Possible candidate CLaRA - Compulsive Liar and Reckless Assistant

## Description

Project Archivist is a tool meant assist the user at organizing and managing internet information. Using a harness and multi-agent architecture. Assumes that the agent WILL hallucinate, be malicious, and have ulterior motives due to prompt injections and other sources of uncertainty.

## Installation

>This project does *NOT* host the LLM.<br>
>An OpenAI API Endpoint will be needed. (e.g. locahost:8080/v1/chat/completions)
>
>Local LLM compute
>- Open-source: [llama.cpp](https://github.com/ggml-org/llama.cpp?tab=readme-ov-file), [vllm](https://github.com/vllm-project/vllm)<br>
>
>Cloud/API: [OpenAI](https://chatgpt.com), [Anthropic](https://claude.ai/)


```sh
# 1. Download repo
git clone https://github.com/DrakeVoong/Project_Archivist.git
cd Project_Archivist

# 2. Install uv
pip install uv

# 3. (Optional) Create environment
uv venv
source .venv\Scripts\activate   # Windows

# 4. Install dependencies
uv sync

# 5. Run setup
# ~/project_archivist/
python src/archivist/core/harness.py
```

## Road Map
Must Do
- Implement logging to track call stack
- Stream tokens into terminal
- turn harness into a class so that it can be used by interfaces
- add find all occurances in multiple files (helpful for large file structures)
- fix find_all_occurances error
    - when an agent tries to call into a directory the full absolute path is exposed to the agent
    - better error handling techniques when returning data to agent

Nice to Do
- Implement an atomic file writing procedure
    - copy file, write to temp file, replace file 