from dataclasses import dataclass
import json
import subprocess
import requests
from typing import Generator, Iterable
from openai import OpenAI
from openai import OpenAI, omit
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionToolUnionParam,
)

from archivist.core.type import SamplingConfig
from archivist.config.settings import settings, LOG_PATH, DATA_PATH
from archivist.llm_providers.provider import Provider


class LlamaCPPServer(Provider):
    def __init__(self, port: str):
        self.llama_server_path = settings.LLAMA_CPP_DIR / "llama-server"
        self.port = port
        self.running = False
        self.log_file = LOG_PATH / "llama_server_log.txt"
        self.API_URL = f"http://127.0.0.1:{self.port}/v1/chat/completions"
        self.client = OpenAI(base_url=f"http://127.0.0.1:{self.port}/v1", api_key="none")
        self.model = "local"

    def _get_config(self):
        config_path = DATA_PATH / "llama_server_config.json"

        if not config_path.exists():
            raise FileNotFoundError(f"File {config_path} not found.")

        with open(config_path) as f:
            config = json.load(f)

        args = []
        for flag, value in config.items():
            if isinstance(value, bool):
                if value:
                    args.append(flag)
            else:
                args.extend([flag, str(value)])

        return args


    def connect(self, config: list):
        """
        Start llama-server in router mode
        """

        command = [self.llama_server_path, "--models-dir", settings.LLMS_DIR, *config]
        # Start llama-server
        with open(self.log_file, 'w') as f:
            self.process = subprocess.Popen(command, stdout=f, stderr=subprocess.STDOUT, text=True)
            self.running = True

        return 1

    def connect_model(self, model:str):
        """
        Start llama-server in direct model loading mode
        """

        command = [self.llama_server_path, 
                   "-m", settings.LLMS_DIR / model, 
                   "--port", self.port, 
                   *self._get_config()
                   ]

        # Execute the llama-server command as a seperate process
        with open(self.log_file, 'w') as f:
            self.process = subprocess.Popen(command, stdout=f, stderr=subprocess.STDOUT, text=True)
            self.running = True

        return 1

    def get_available_models(self):
        """
        Not Implemented yet
        """
        if not self.running:
            return -1
        
    def generate(self, messages:list[dict[str,str]]):
        """
        Generate an LLM response using requests module
        """
        data = {
            "messages": messages,
            "stream": False,
            "temperature": 0.9,
            "top_p": 0.9,
            "top_k": 40,
            "min_p": 0,
        }

        response = requests.post(self.API_URL, json=data)
        response.raise_for_status()
        return response.json()

    def generate_openai(self, messages: Iterable[ChatCompletionMessageParam], sampling_config:SamplingConfig, 
                        tools: Iterable[ChatCompletionToolUnionParam] | None = None) -> ChatCompletion:
        response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools if tools else omit,
                # Sampling
                temperature=sampling_config.temperature,
                top_p=sampling_config.top_p,
                presence_penalty=sampling_config.presence_penalty,
                extra_body=sampling_config.get_openai_llamacpp_kwargs()
                )
        return response

    def generate_stream(self, messages:str) -> Generator:
        payload = {"messages": messages, "stream": True}
        with requests.post(self.API_URL, json=payload, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data = line[len("data: "):]
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    yield chunk

    def get_status(self):
        if self.port == -1:
            print("Llama server is not running")
            return 404

        try:
            response = requests.get(f"http://127.0.0.1:{self.port}/health", stream=False)
        except requests.exceptions.ConnectionError as e:
            print(f"Error connecting to llama-server: {e}")
            return 404

        if response.status_code == 503:
            print("llama-server still loading")
            return 503
        else:
            print("llama-server is ready")
            return 200

    def disconnect(self):
        """
        Stop llama-server
        """
        if self.running and self.process:
            self.process.terminate()
            self.process.wait()
            self.running = False

    def __del__(self):
        self.disconnect()