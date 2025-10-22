# Project Archivist

## Description

Project Archivist is a tool meant to help, organize, and manage internet information. With the use of workflow/diagram, allows the user to customize the specific steps of their own AI agents. 

## Installation

>This project does *NOT* host the LLM.<br>
>An OpenAI API Endpoint will be needed. (e.g. /v1/chat/completions)
>
>Local LLM compute
>- Open-source: [llama.cpp](https://github.com/ggml-org/llama.cpp?tab=readme-ov-file), [vllm](https://github.com/vllm-project/vllm)<br>
>- Closed-source: [LM Studio](https://lmstudio.ai/)<br>
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
source .venv/bin/activate       # Linux/macOS
source .venv\Scripts\activate   # Windows

# 4. Install dependencies
uv sync

# 5. Run setup
python setup.py
```

## Road Map
- [ ] Complete workflow functions
- [ ] Vector databases integration with agents
- [ ] Add wikipedia knowledge

## Future Features
- Simulate conversation with other agents to allow primary agent to "grow" and "learn" from experiences over time
- Tag based storage for fast and efficient searching of personal documents, internet information, videos, etc
