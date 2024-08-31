import bpy
import json

class ExportJSONOperator(bpy.types.Operator):
    """Export JSON data from the active object's collection"""
    bl_idname = "export.json_data"
    bl_label = "Export JSON"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        self.export_plg_json_from_active_object(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def export_plg_json_from_active_object(self, file_path):
        active_obj = bpy.context.active_object
        if not active_obj:
            self.report({'ERROR'}, "No active object selected.")
            return

        if active_obj.users_collection:
            collection = active_obj.users_collection[0]
        else:
            self.report({'ERROR'}, "Active object is not in any collection.")
            return

        json_structure = [{
            "Type": "PlgAsset",
            "Name": collection.name,
            "Class": "UScriptClass'PlgAsset'",
            "Properties": {
                "PlgData": {
                    "PlgDatas": []
                }
            }
        }]

        for obj in collection.objects:
            if obj.type == 'MESH':
                vertices = [{"X": round(vert.co.x, 4), "Y": round(vert.co.y, 4), "Z": round(vert.co.z, 4)} for vert in obj.data.vertices]
                indices = [vertex for poly in obj.data.polygons for vertex in poly.vertices]

                # Initialize colors list
                colors = [0 for _ in vertices]
                color_layer = obj.data.vertex_colors.active
                if color_layer:
                    for poly in obj.data.polygons:
                        for loop_index in poly.loop_indices:
                            loop_vert_index = obj.data.loops[loop_index].vertex_index
                            vert_color = color_layer.data[loop_index].color
                            if vert_color[:3] == (0, 0, 0):  # Check for black color
                                colors[loop_vert_index] = 4294967040
                            elif vert_color[:3] == (1, 1, 1):  # Check for white color
                                colors[loop_vert_index] = 4294967295

                # Calculate bounding box
                xs = [v["X"] for v in vertices]
                ys = [v["Y"] for v in vertices]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)

                section = {
                    "Vertices": vertices,
                    "Indices": indices,
                    "Colors": colors,
                    "Name": obj.name,
                    "MinX": min_x,
                    "MinY": min_y,
                    "MaxX": max_x,
                    "MaxY": max_y
                }

                json_structure[0]["Properties"]["PlgData"]["PlgDatas"].append(section)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_structure, f, ensure_ascii=False, indent=2)

def menu_func_export(self, context):
    self.layout.operator(ExportJSONOperator.bl_idname, text="Export JSON")

def register():
    bpy.utils.register_class(ExportJSONOperator)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportJSONOperator)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
