# Project Archivist

Project name to be determined.  
Possible candidate CLaRA - Complusive Liar and Reckless Assistant

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
