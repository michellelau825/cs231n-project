import sys
import json
import bpy
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: blender --background --python generate_blend_from_json.py -- <primitives.json>")
        sys.exit(1)
    try:
        idx = sys.argv.index("--")
        json_path = sys.argv[idx + 1]
    except (ValueError, IndexError):
        print("Error: JSON file path required after '--'")
        sys.exit(1)

    with open(json_path, "r") as f:
        specs = json.load(f)

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    for i, spec in enumerate(specs):
        op = spec["operation"]
        params = spec["params"]
        transform = spec.get("transform", {})
        obj = None

        if op == "build_prism_mesh":
            n = params.get("n", 8)
            r = params.get("r_max", 1)
            h = params.get("height", 1)
            bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=h)
            obj = bpy.context.active_object
        elif op == "bezier_curve":
            anchors = params.get("anchors", [[0,0,0],[1,0,0]])
            curve_data = bpy.data.curves.new('curve', type='CURVE')
            curve_data.dimensions = '3D'
            polyline = curve_data.splines.new('POLY')
            polyline.points.add(len(anchors)-1)
            for j, coord in enumerate(anchors):
                polyline.points[j].co = (*coord, 1)
            obj = bpy.data.objects.new('curve_obj', curve_data)
            bpy.context.collection.objects.link(obj)

        if obj and transform:
            if "location" in transform:
                obj.location = transform["location"]
            if "rotation" in transform:
                obj.rotation_euler = transform["rotation"]
            if "scale" in transform:
                obj.scale = transform["scale"]

    out_path = Path(json_path).with_suffix('.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(out_path))
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    main() 