import inspect
from pathlib import Path
import re

from archivist.config.settings import PROJECT_ROOT, resolve_path

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

# -------- File/Folders ---------
# For now the agent can only access paths in this project (whitelist protection)
# PROJECT_ROOT


@tool
def read_file(relative_path: str, offset:int = 0) -> str:
    """
    Read a file and return the 4096 characters.
    You can set an offset amount, but the default is 0.

    Use this when you need the text of a file on disk.  
    While you are continually reading the file (calling read_file() in succession) set the offset to increments of 4096, so that the overlapping characters do not overfill your context window.
    """
    full_path = resolve_path(relative_path)

    if full_path.is_dir():
        raise IsADirectoryError(f"Expected a file, got a directory: {relative_path}")

    with open(full_path) as f:
        f.seek(offset)
        return f.read(4096)

@tool
def find_all_occurances_in_file(relative_path: str, substring:str) -> list[int]:
    """
    This will find all occurances of a substring inside of a file.  
    Which will then return a list of int of all locations (character-by-character) of that substring.

    Use this when you need to find a specific name, variable, function, etc. in a file without having to manually scan the entire file with read_file.
    """
    full_path = resolve_path(relative_path)

    if full_path.is_dir():
        raise IsADirectoryError(f"Expected a file, got a directory: {relative_path}")

    with open(full_path) as f:
        contents = f.read()

    positions = [match.start() for match in re.finditer(substring, contents)]

    return positions


# @tool
def edit_file(relative_path:str, old_str:str, new_str:str) -> bool:
    """
    Edit a file by replacing the old text with the new desired text.  
    old_str must match EXACTLY to a section of text in the file.  
    This will replace ALL occurances of old_str.  
    This will return True for success.  

    Use this when you need to edit a file, you must read the file first.
    """
    full_path = resolve_path(relative_path)

    if full_path.is_dir():
        raise IsADirectoryError(f"Expected a file, got a directory: {relative_path}")

    with open(full_path) as f:
        contents = f.read()
        new_contents = contents.replace(old_str, new_str)

    with open(full_path, "w") as f:
        f.write(new_contents)

    if contents != new_contents:
        return True
    else:
        return False

@tool
def ls(relative_path:str) -> list:
    """
    Get the files and folders in a directory. Similar to ls command

    Use this when you need to explore the contents of an unknown folder.
    """
    full_path = resolve_path(relative_path)

    return sorted(x.name for x in full_path.iterdir())

@tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b