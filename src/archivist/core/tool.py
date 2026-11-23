import inspect

TOOLS = {}

TYPE_MAP = {
    int: "integer",
    float: "number",
    str: "string",
    bool: "boolean",
    list: "array",
    dict: "object",
}

def tool(fn):
    doc = inspect.getdoc(fn)
    if not doc:
        raise ValueError(f"Tool '{fn.__name__}' needs a docstring")

    properties, required = {}, []
    # Loop for every parameter in the function
    for name, param in inspect.signature(fn).parameters.items():
        json_type = TYPE_MAP.get(param.annotation) # Get the type of the parameter 
        if json_type is None:
            raise ValueError(f"Tool '{fn.__name__}': param '{name}' needs a supported type hint")
        properties[name] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(name)

    TOOLS[fn.__name__] = {
        "fn": fn,
        "schema": {
            "type": "function",
            "function": {
                "name": fn.__name__,
                "description": doc,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        },
    }
    return fn

def get_tools():
    return [t["schema"] for t in TOOLS.values()]

def call_tool(name, args):
    if name not in TOOLS:
        return f"Unknown tool: {name}"
    try:
        return str(TOOLS[name]["fn"](**args))
    except Exception as e:
        return f"Error: {e}"

@tool
def read_file(path: str) -> str:
    """
    Read a file and return its contents.

    Use this when you need the full text of a file on disk.
    """
    with open(path) as f:
        return f.read()

@tool
def edit_file(path:str, old_str:str, new_str:str) -> bool:
    """
    Edit a file by replacing the old text with the new desired text.  
    old_str must match EXACTLY to a section of text in the file.  
    This will replace ALL occurances of old_str.  
    This will return True for success.  

    Use this when you need to edit a file, you must read the file first.
    """

    with open(path) as f:
        contents = f.read()
        new_contents = contents.replace(old_str, new_str)

    with open(path, "w") as f:
        f.write(new_contents)

    if contents != new_contents:
        return True
    else:
        return False

@tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b