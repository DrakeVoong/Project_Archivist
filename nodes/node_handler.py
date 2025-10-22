from typing import get_args
import os
import importlib

NODE_REGISTRY = {}

def node(inputs=None, settings=None, outputs=None, trigger_inputs=None, send_outputs=None):
    def wrap(func):
        func_data = func.__annotations__    

        # Get function trigger inputs into {"name": type} format
        # For example, on_message() would need message, address, and type from the webui to be able
        # to properly send data to next nodes
        node_trigger_inputs = {}
        if trigger_inputs is not None:
            for index, (arg, type_hint) in enumerate(func_data.items()):
                if arg in trigger_inputs:
                    if hasattr(type_hint, "__name__"):
                        node_trigger_inputs[arg] = type_hint.__name__
                    else:
                        node_trigger_inputs[arg] = type_hint


        # Get function outputs into {"name": type} format
        node_outputs = {}
        function_send_outputs = {}
        if "return" in func_data and (outputs is not None or send_outputs is not None):
            return_values = list(get_args(func_data["return"]))

            global_index = 0
            # Get all outputs that will become node ports
            if outputs is not None:
                for index, output_name in enumerate(outputs):
                    output_type = return_values[index]
                    if hasattr(output_type, "__name__"):
                        node_outputs[output_name] = output_type.__name__
                    else: # generic type i.e. List[int]
                        node_outputs[output_name] = str(output_type).split(".")[1]

                global_index += index

            # Get all outputs that will be returned outside of the loop
            # For uses such as passing to a flask route function for streaming messages
            if send_outputs is not None:
                for index, output_name in enumerate(send_outputs):
                    output_type = return_values[global_index + index] 
                    if hasattr(output_type, "__name__"):
                        function_send_outputs[output_name] = output_type.__name__
                    else: # generic type i.e. List[int]
                        function_send_outputs[output_name] = str(output_type).split(".")[1]

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
            "outputs": node_outputs or {},
            "trigger_inputs": node_trigger_inputs or {},
            "send_outputs": function_send_outputs or {}
        }

        func._node_meta = node_metadata

        node_path = f"{module_location}.{func.__qualname__}"
        NODE_REGISTRY[node_path] = node_metadata
        return func
    return wrap

def import_nodes():
    """
    Searches for all python files in nodes dir and imports them, so that no main file editing
    needs to be done to add new nodes
    """
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
