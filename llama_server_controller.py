import requests
import os
import subprocess
import signal
import psutil

import settings

class LlamaServerController:
    """
    Starts and stops llama server

    Attributes:
        llama_server_path (str): The path to the llama-server executable.
        output_file (str): The path to the output file for logging.
        port (int): The port to run llama-server on. Default is 5050.
    """
    def __init__(self, llama_server_path, port = 5050):
        self.llama_server_path = llama_server_path
        self.output_file = os.path.join(settings.MAIN_DIR, "llama_server_log.txt")
        self.running = False
        self.port = port
        self.API_URL = f'http://localhost:{self.port}/v1/chat/completions'

    def run(self, vision : bool, llm_path : str, devices : str = "cuda0", *args):
        """
        Start llama server
        """
        print("Controller starting up...")
        # TODO: Add model settings support
        command = [self.llama_server_path,
                    "--model", llm_path,
                    "--port", str(self.port),
                    "--device", devices,
                    "-t", "7",
                    "-ncmoe", "10",
                    "-b", "2048", 
                    "-ub", "1024",
                    "-ctk", "q8_0", # TODO: Add support for custom quatization
                    "-ctv", "q8_0",
                    "-ngl", "49",
                    "--no-mmap",
                    "-fa", "1",
                    "-c", "32768"]
        
        # Support for vision
        if vision:
            command.append("--mmproj")
            command.append(args[0])
        
        # Support for multiple GPUs
        if ','  in devices:
            command.append("-ts")
            command.append("3,3")

        # Start llama-server
        with open(self.output_file, 'w') as f:
            self.process = subprocess.Popen(command, stdout=f, stderr=subprocess.STDOUT, text=True)
            self.running = True

    def get_health(self):
        """
        Check status of llama-server

        Returns:
            int: 200 if llama-server is running, 404 if not, 503 if still loading.
        """
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

    def terminate(self):
        """
        Kills all llama-server processes
        """
        process_name = "llama-server"

        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process_name.lower():
                os.kill(proc.info['pid'], signal.SIGTERM)
                print(f"Killed llama-server with {proc.info['pid']} PID")
