from typing import get_args
import os
import importlib

NODE_REGISTRY = {}

def node(inputs=None, settings=None, outputs=None):
    def wrap(func):
        func_data = func.__annotations__        

        # Get function outputs into {"name": type} format
        node_outputs = {}
        if "return" in func_data and outputs is not None:
            if str(func_data["return"]).startswith("typing.Generator"):
                node_outputs[outputs[0]] = "Generator"
            else:
                for index, output in enumerate(get_args(func_data["return"])):
                    if hasattr(output, "__name__"):
                        node_outputs[outputs[index]] = output.__name__
                    else: # generic type i.e. List[int]
                        node_outputs[outputs[index]] = str(output).split(".")[1]

        # Get function settings into {"name": type} format
        node_settings = {}
        if settings is not None:
            for index, (arg, type_hint) in enumerate(func_data.items()):
                if arg in settings:
                    if hasattr(type_hint, "__name__"):
                        node_settings[arg] = type_hint.__name__
                    else:
                        node_settings[arg] = type_hint

        # Get function inputs into {"name": type_hint} format
        node_inputs =  {}
        if inputs is not None:
            for index, (arg, type_hint) in enumerate(func_data.items()):
                if arg in inputs:
                    if hasattr(type_hint, "__name__"):
                        node_inputs[arg] = type_hint.__name__
                    else:
                        node_inputs[arg] = type_hint

        module_location = func.__module__[len("nodes."):]

        node_metadata = {
            "callable": func,
            "name": func.__qualname__,
            "module": module_location,
            "inputs": node_inputs or {},
            "settings": node_settings or {},
            "outputs": node_outputs or {}
        }

        func._node_meta = node_metadata

        node_path = f"{module_location}.{func.__qualname__}"
        NODE_REGISTRY[node_path] = node_metadata
        return func
    return wrap

def import_nodes():
    for dirpath, dirnames, files in os.walk("nodes"):
        for file in files:
            if file.endswith(".py") and file != "__init__.py" and file != "node_handler.py":
                python_file = os.path.join(dirpath, file[:-len(".py")])
                import_name = python_file.replace(os.sep, ".")

                try:
                    importlib.import_module(import_name)
                except Exception as e:
                    print(f"Error importing: {import_name} Error: {e}")

if __name__ == "__main__":
    import_nodes()
