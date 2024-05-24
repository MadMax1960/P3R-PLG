import bpy
import json
import os

class ImportJSONOperator(bpy.types.Operator):
    """Import JSON"""
    bl_idname = "import.json"
    bl_label = "Import JSON"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        self.import_json(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def import_json(self, json_file_path):
        json_file_name = os.path.basename(json_file_path)
        collection_name = os.path.splitext(json_file_name)[0]  # Use the file name without extension as the collection name

        # Read the JSON data
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        # Check if the collection already exists. If not, create it.
        if collection_name not in bpy.data.collections:
            new_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(new_collection)
        else:
            new_collection = bpy.data.collections[collection_name]

        # Function to create a new mesh and link it to the specified collection
        def create_mesh(vertices, faces, name, collection):
            mesh_data = bpy.data.meshes.new(name + "_mesh")
            mesh_data.from_pydata(vertices, [], faces)
            mesh_data.update()

            obj = bpy.data.objects.new(name, mesh_data)
            collection.objects.link(obj)

        for section_index, section in enumerate(data[0]['Properties']['PlgData']['PlgDatas']):
            vertices = [(vertex['X'], vertex['Y'], vertex['Z']) for vertex in section['Vertices']]
            faces = []
            if 'Indices' in section:
                indices = section['Indices']
                try:
                    if isinstance(indices[0], int):
                        for i in range(0, len(indices), 3):
                            face = (indices[i], indices[i+1], indices[i+2])
                            faces.append(face)
                    elif isinstance(indices[0], list):
                        for index_group in indices:
                            face = tuple(index for index in index_group)
                            faces.append(face)
                except Exception as e:
                    print(f"Error processing indices in section {section_index}:", e)

            section_name = section.get("Name", f"PLG_Section_{section_index}")
            create_mesh(vertices, faces, section_name, new_collection)

def menu_func_import(self, context):
    self.layout.operator(ImportJSONOperator.bl_idname, text="Import JSON")
