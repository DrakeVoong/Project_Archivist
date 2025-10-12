from typing import get_args
import os
import importlib

NODE_REGISTRY = {}

def node(inputs=None, settings=None, outputs=None):
    def wrap(func):
        func_data = func.__annotations__        
        # Get function outputs into {"name": type} format
        node_outputs = {}
        if "return" in func_data:
            for index, output in enumerate(get_args(func_data["return"])):
                if hasattr(output, "__name__"):
                    node_outputs[outputs[index]] = output.__name__
                else: # generic type i.e. List[int]
                    node_outputs[outputs[index]] = str(output).split(".")[1]

        # Get function settings into {"name": type} format
        node_settings = {}
        for index, (arg, type) in enumerate(func_data.items()):
            if arg in settings:
                node_settings[arg] = type

        # Get function inputs into {"name": type} format
        node_inputs =  {}
        if inputs is not None:
            for index, (arg, type) in enumerate(func_data.items()):
                if arg in inputs:
                    node_inputs[arg] = type

        node_metadata = {
            "callable": func,
            "name": func.__qualname__,
            "module": func.__module__,
            "inputs": node_inputs or {},
            "settings": node_settings or {},
            "outputs": node_outputs or {}
        }

        func._node_meta = node_metadata

        node_path = f"{func.__module__}.{func.__qualname__}"
        NODE_REGISTRY[node_path] = node_metadata
        # print(func._node_meta)
        return func
    return wrap

def import_nodes():
    for dirpath, dirnames, files in os.walk("nodes"):
        for file in files:
            if file.endswith(".py") and file != "__init__.py" and file != "node_handler.py":
                python_file = os.path.join(dirpath, file[:-len(".py")])
                import_name = python_file.replace(os.sep, ".")
                print(import_name)

                try:
                    importlib.import_module(import_name)
                except Exception as e:
                    print(f"Error importing: {import_name} Error: {e}")

if __name__ == "__main__":
    import_nodes()
