bl_info = {
    "name": "PLG Import/Export",
    "blender": (2, 80, 0),
    "category": "Import-Export",
    "version": (1, 0, 0),
    "author": "Mudkip, Adrien",
    "description": "Import and Export PLG JSON files",
}

import bpy
import os
import importlib.util

# Function to dynamically import Python modules (import.py and export.py) based on filepath
def import_module_from_filepath(module_name, filepath):
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Directory of the current plugin file
current_dir = os.path.dirname(os.path.realpath(__file__))

# Loading the import and export py
import_py = import_module_from_filepath("import_py", os.path.join(current_dir, "import.py"))
export_py = import_module_from_filepath("export_py", os.path.join(current_dir, "export.py"))

def register():
    bpy.utils.register_class(import_py.ImportJSONOperator)
    bpy.utils.register_class(export_py.ExportJSONOperator)
    bpy.types.TOPBAR_MT_file_import.append(import_py.menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(export_py.menu_func_export)

def unregister():
    bpy.utils.unregister_class(import_py.ImportJSONOperator)
    bpy.utils.unregister_class(export_py.ExportJSONOperator)
    bpy.types.TOPBAR_MT_file_import.remove(import_py.menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(export_py.menu_func_export)

if __name__ == "__main__":
    register()
