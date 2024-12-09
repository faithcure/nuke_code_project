import json
import os
import nuke
from editor.core import PathFromOS

# Function to retrieve Nuke functions.
def get_nuke_functions():
    """Returns the name, type, and documentation information of Nuke functions."""
    nuke_functions = []
    if nuke:
        for func_name in dir(nuke):
            func = getattr(nuke, func_name)
            if callable(func):
                nuke_functions.append({
                    "name": func_name,
                    "type": "Function",
                    "doc": func.__doc__ or "No documentation available."
                })
            elif isinstance(func, (nuke.Knob, nuke.Node)):
                nuke_functions.append({
                    "name": func_name,
                    "type": "Knob" if isinstance(func, nuke.Knob) else "Node",
                    "doc": func.__doc__ or "No documentation available."
                })
    return nuke_functions

# Write Nuke functions to a JSON file
def update_nuke_functions():
    """Writes functions from Nuke to a JSON file."""
    nuke_functions = get_nuke_functions()

    # Directory where the JSON file will be stored
    json_dir = os.path.join(PathFromOS().assets_path, 'dynamic_data')

    # Create the dynamic_data directory if it doesn't exist
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    json_path = os.path.join(json_dir, 'nuke_functions.json')

    # Open the file in write mode and update the content
    with open(json_path, 'w') as json_file:
        json.dump(nuke_functions, json_file, indent=4)

# Load Nuke functions from a JSON file
def load_nuke_functions():
    """Loads Nuke functions from a JSON file. Updates the file if it doesn't exist."""
    json_path = os.path.join(PathFromOS().assets_path, 'dynamic_data', 'nuke_functions.json')

    # If the JSON file doesn't exist, update it
    if not os.path.exists(json_path):
        update_nuke_functions()

    # Open the JSON file and return its content
    with open(json_path, 'r') as json_file:
        return json.load(json_file)
