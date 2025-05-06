import bpy
import json
import os


class ExportJSONOperator(bpy.types.Operator):
    """Export JSON data from the active object's collection and a companion text file in Y‑JSON format."""
    bl_idname = "export.json_data"
    bl_label = "Export JSON" 
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        json_path = self.filepath
        if not json_path.lower().endswith(".json"):
            json_path += ".json"

        self.export_plg_json_from_active_object(json_path)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def triangulate_mesh(self, obj):
        """Convert all quads/ngons in *obj* to triangles (in‑place)."""
        if obj.type == 'MESH':
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.quads_convert_to_tris()
            bpy.ops.object.mode_set(mode='OBJECT')

    def convert_color_to_format(self, r, g, b, a=1.0):
        """Pack RGBA floats (0‑1) into a 32‑bit ARGB integer."""
        r_i = max(0, min(int(r * 255), 255))
        g_i = max(0, min(int(g * 255), 255))
        b_i = max(0, min(int(b * 255), 255))
        a_i = max(0, min(int(a * 255), 255))
        return (a_i << 24) | (r_i << 16) | (g_i << 8) | b_i

    def generate_yjson_true_format(self, x_data):
        plgdatas = x_data[0]["Properties"]["PlgData"]["PlgDatas"]
        result = "(PlgDatas=("
        for data in plgdatas:
            vertices = ",".join(
                f"(X={v['X']:.6f},Y={v['Y']:.6f},Z={v['Z']:.6f})" for v in data["Vertices"]
            )
            indices = ",".join(str(i) for i in data["Indices"])
            colors = ",".join(str(c) for c in data["Colors"])
            name = data["Name"]
            minx, miny, maxx, maxy = data["MinX"], data["MinY"], data["MaxX"], data["MaxY"]
            result += (
                f"(Vertices=({vertices}),"
                f"Indices=({indices}),"
                f"Colors=({colors}),"
                f"Name=\"{name}\"," \
                f"MinX={minx:.6f},MinY={miny:.6f},MaxX={maxx:.6f},MaxY={maxy:.6f}),"
            )
        return result.rstrip(',') + "))"

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
            if obj.type != 'MESH':
                continue

            if len(obj.data.vertices) == 0 or len(obj.data.polygons) == 0:
                json_structure[0]["Properties"]["PlgData"]["PlgDatas"].append({
                    "Vertices": [],
                    "Indices": [],
                    "Colors": [],
                    "Name": obj.name if obj.name else "None",
                    "MinX": 0.0,
                    "MinY": 0.0,
                    "MaxX": 0.0,
                    "MaxY": 0.0
                })
                self.report({'WARNING'}, f"Object '{obj.name}' is empty. Added a dummy entry.")
                continue

            self.triangulate_mesh(obj)

            vertices = [{"X": round(v.co.x, 4), "Y": round(v.co.y, 4), "Z": round(v.co.z, 4)} for v in obj.data.vertices]
            indices = [v for p in obj.data.polygons for v in p.vertices]

            colors = [0] * len(vertices)
            color_layer = obj.data.vertex_colors.active
            if color_layer:
                for poly in obj.data.polygons:
                    for loop_index in poly.loop_indices:
                        vi = obj.data.loops[loop_index].vertex_index
                        colors[vi] = self.convert_color_to_format(*color_layer.data[loop_index].color)

            xs = [v["X"] for v in vertices]
            ys = [v["Y"] for v in vertices]
            json_structure[0]["Properties"]["PlgData"]["PlgDatas"].append({
                "Vertices": vertices,
                "Indices": indices,
                "Colors": colors,
                "Name": obj.name,
                "MinX": min(xs),
                "MinY": min(ys),
                "MaxX": max(xs),
                "MaxY": max(ys)
            })

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_structure, f, ensure_ascii=False, indent=2)

        txt_path = os.path.splitext(file_path)[0] + ".txt"
        yjson_string = self.generate_yjson_true_format(json_structure)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(yjson_string)

        self.report({'INFO'}, f"Exported: {file_path} and {txt_path}")

    def report(self, type, message):
        print(f"{type}: {message}")



def menu_func_export(self, context):
    self.layout.operator(ExportJSONOperator.bl_idname, text="Export PLG JSON")


def register():
    bpy.utils.register_class(ExportJSONOperator)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportJSONOperator)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
