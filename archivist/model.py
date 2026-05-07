import requests
import json


class Model:
    def __init__(self):
        pass
            
    def generate(self, conversation, controller, settings: dict) -> str:
        """
        Generates a response from the model using the conversation history and settings.

        Args:
            conversation (dict): Conversation in OpenAI Completion API format
            controller (LlamaServerController): LlamaServerController object
            settings (dict): Settings for the model

        Returns:
            str: Response from the model

        Raises:
            Exception: Failure returned by llama-server. Usually malformed conversation or settings.
        """

        # Send prompt and settings to llama-server
        response = requests.post(
            controller.API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "messages": conversation,
                "stream": False,
                "temperature": settings["temperature"],
                "top_p": settings["top_p"],
                "top_k": settings["top_k"],
                "min_p": settings["min_p"],
                "frequency_penalty": settings["frequency_penalty"],
                "presence_penalty": settings["presence_penalty"],
            }, 
            stream=True)

        total = ""
        # Return response from llama-server
        if response.status_code == 200:
            data = response.json() 
            return data["choices"][0]["message"]["content"]
        else:
            print(f"Error: {response.status_code}")
            return response.status_code

    def generate_stream(self, conversation : dict, controller, settings: dict):
        """
        Generates a response from the model using the conversation history and settings.

        Args:
            conversation (dict): Conversation in OpenAI Completion API format
            controller (LlamaServerController): LlamaServerController object
            settings (dict): Settings for the model

        Yields:
            str: Response from the model in tokens.

        Raises:
            Exception: Failure returned by llama-server. Usually malformed conversation or settings.
        """
        # Send prompt and settings to llama-server
        response = requests.post(
            controller.API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "messages": conversation,
                "stream": True,
                "temperature": settings["temperature"],
                "top_p": settings["top_p"],
                "top_k": settings["top_k"],
                "min_p": settings["min_p"],
                "frequency_penalty": settings["frequency_penalty"],
                "presence_penalty": settings["presence_penalty"],
            }, 
            stream=True)

        total = ""
        if response.status_code == 200:
            # 
            for line in response.iter_lines():
                if line:
                    # Decode line from bytes to string
                    try:
                        decoded_line = line.decode('utf-8')
                    except UnicodeDecodeError:
                        print(f"\nWarning: Could not decode line as UTF-8: {line}")
                        continue
                    
                    # Get dict data 
                    if decoded_line.startswith("data: "):
                        try:
                            data_json = json.loads(decoded_line[6:])
                        except json.JSONDecodeError:
                            print(f"\nError decoding JSON: {decoded_line}")
                            continue
                        
                        # End of stream
                        if data_json["choices"][0]["finish_reason"] == "stop":
                            yield data_json["timings"]["predicted_n"], True
                            break
                        
                        # The token string generated
                        delta_content = data_json["choices"][0]["delta"].get("content", "")
                        if delta_content:
                            yield delta_content, False
        else:
            print(f"Error: {response.status_code}")
            return response.status_code

