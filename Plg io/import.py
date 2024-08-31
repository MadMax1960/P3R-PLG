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

        # Create black and white materials
        black_material = bpy.data.materials.new(name="Black_Material")
        black_material.diffuse_color = (0, 0, 0, 1)
        
        white_material = bpy.data.materials.new(name="White_Material")
        white_material.diffuse_color = (1, 1, 1, 1)

        # Function to create a new mesh and link it to the specified collection
        def create_mesh(vertices, faces, colors, name, collection):
            mesh_data = bpy.data.meshes.new(name + "_mesh")
            mesh_data.from_pydata(vertices, [], faces)
            mesh_data.update()

            obj = bpy.data.objects.new(name, mesh_data)
            collection.objects.link(obj)

            # Assign materials based on vertex colors
            obj.data.materials.append(black_material)
            obj.data.materials.append(white_material)

            # Create a vertex color layer
            color_layer = mesh_data.vertex_colors.new(name="Col")

            for poly in mesh_data.polygons:
                for loop_index in poly.loop_indices:
                    loop_vert_index = mesh_data.loops[loop_index].vertex_index
                    color_value = colors[loop_vert_index]

                    # Assign vertex colors
                    if color_value == 4294967295:
                        color_layer.data[loop_index].color = (1.0, 1.0, 1.0, 1.0)
                    elif color_value == 4294967040:
                        color_layer.data[loop_index].color = (0.0, 0.0, 0.0, 1.0)
                    else:
                        color_layer.data[loop_index].color = (0.5, 0.5, 0.5, 1.0)

            # Assign materials to faces based on the vertex color
            for poly in mesh_data.polygons:
                white_count = sum(1 for loop_index in poly.loop_indices if color_layer.data[loop_index].color == (1.0, 1.0, 1.0, 1.0))
                black_count = sum(1 for loop_index in poly.loop_indices if color_layer.data[loop_index].color == (0.0, 0.0, 0.0, 1.0))

                if white_count > black_count:
                    poly.material_index = 1  # White material
                else:
                    poly.material_index = 0  # Black material

        for section_index, section in enumerate(data[0]['Properties']['PlgData']['PlgDatas']):
            vertices = [(vertex['X'], vertex['Y'], vertex['Z']) for vertex in section['Vertices']]
            colors = section.get('Colors', [])
            
            # Check if the length of colors matches the length of vertices
            if len(colors) != len(vertices):
                print(f"Warning: Number of colors ({len(colors)}) does not match number of vertices ({len(vertices)}) in section {section_index}")
                # Pad the colors list with zeros if not matching
                colors = colors + [0] * (len(vertices) - len(colors))

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
            create_mesh(vertices, faces, colors, section_name, new_collection)

def menu_func_import(self, context):
    self.layout.operator(ImportJSONOperator.bl_idname, text="Import JSON")

# Register the operator and menu
def register():
    bpy.utils.register_class(ImportJSONOperator)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportJSONOperator)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
