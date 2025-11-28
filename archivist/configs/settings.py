import os
import json
import sys


# Paths
MAIN_DIR = os.getcwd()
CONV_DIR = os.path.join(MAIN_DIR, "vectors", "conv")
MEMORY_DIR = os.path.join(MAIN_DIR, "memory")
AGENT_DIR = os.path.join(MAIN_DIR, "agent")

# Config
with open(os.path.join(MAIN_DIR, "config.json"), "r") as file:
    config = json.load(file)

must_includes = 0

# Check if all required paths are in config.json
if "llama.cpp_dir" in config:
    LLAMA_CPP_DIR = config["llama.cpp_dir"]
else:
    print("llama.cpp not found in config.json")
    LLAMA_CPP_DIR = None
    must_includes += 1

if "llms_dir" in config:
    LLMS_DIR = config["llms_dir"]
else:
    print("LLM directory not found in config.json")
    LLMS_DIR = None
    must_includes += 1

if "sentence_model_dir" in config:
    SENTENCE_MODEL_DIR = config["sentence_model_dir"]
else:
    print("Sentence model directory not found in config.json")
    SENTENCE_MODEL_DIR = None
    must_includes += 1

if must_includes > 0:
    print("Please add all required paths to config.json")
    sys.exit(1)