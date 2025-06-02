#!/usr/bin/env python3

import sys
import os
import json
import traceback
from pathlib import Path
from typing import Any, Dict

# script_dir    = Path(__file__).parent                                   # …/cs231n-project/infinigen/primitive_builder
# repo_root     = script_dir.parent.parent                                  # …/cs231n-project
# infinigen_dir = repo_root / "infinigen"                                   # …/cs231n-project/infinigen

# for candidate in (str(repo_root), str(infinigen_dir)):
#     if candidate not in sys.path:
#         sys.path.insert(0, candidate)

# Get the project root directory (cs231n-project)
project_root = Path(__file__).parent.parent.parent

# Add project root to Python path
sys.path.insert(0, str(project_root))

# print(">>> After inserting repo_root & infinigen_dir, Blender sys.path is:")
# for p in sys.path:
#     print("    ", p)
# print(">>> End of updated sys.path\n")

# ─── Blender & NumPy imports ──────────────────────────────────────────────────────────────────
try:
    import bpy
    import bmesh
except Exception:
    print("ERROR: Could not import `bpy` or `bmesh`. Run via Blender's Python.")
    raise

try:
    import numpy as np
except Exception:
    print("ERROR: Could not import `numpy`. Install into Blender's Python environment.")
    raise

try:
    from infinigen.core.util import blender as butil
    from infinigen.assets.utils import draw as draw_utils
except Exception:
    print("WARNING: Could not import parts of `infinigen`. JSON references to butil/draw_utils will fail.")
    butil = None
    draw_utils = None

def add_bmesh_cube(name: str = "Cube",
                   size: float = 1.0,
                   location=(0.0, 0.0, 0.0),
                   rotation=(0.0, 0.0, 0.0),
                   scale=(1.0, 1.0, 1.0)) -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size)
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    return obj

def add_bmesh_cylinder(name: str = "Cylinder",
                       radius: float = 1.0,
                       depth: float = 2.0,
                       location=(0.0, 0.0, 0.0),
                       rotation=(0.0, 0.0, 0.0),
                       scale=(1.0, 1.0, 1.0),
                       verts: int = 32) -> bpy.types.Object:
    bm = bmesh.new()
    # Now use radius1/radius2 instead of diameter1/diameter2
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=verts,
        radius1=radius,
        radius2=radius,
        depth=depth
    )
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    return obj

def add_bmesh_uv_sphere(name: str = "UVSphere",
                        radius: float = 1.0,
                        location=(0.0, 0.0, 0.0),
                        rotation=(0.0, 0.0, 0.0),
                        scale=(1.0, 1.0, 1.0),
                        segments: int = 32,
                        rings: int = 16) -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=segments,
        v_segments=rings,
        radius=radius
    )
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    return obj

def add_bmesh_cone(name: str = "Cone",
                   radius1: float = 1.0,
                   radius2: float = 0.0,
                   depth: float = 2.0,
                   location=(0.0, 0.0, 0.0),
                   rotation=(0.0, 0.0, 0.0),
                   scale=(1.0, 1.0, 1.0),
                   segments: int = 32) -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius1,
        radius2=radius2,
        depth=depth
    )
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    return obj

def add_bmesh_torus(name: str = "Torus",
                    major_radius: float = 1.0,
                    minor_radius: float = 0.25,
                    location=(0.0, 0.0, 0.0),
                    rotation=(0.0, 0.0, 0.0),
                    scale=(1.0, 1.0, 1.0),
                    major_segments: int = 48,
                    minor_segments: int = 12) -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_torus(
        bm,
        abso_major_rad=major_radius,
        abso_minor_rad=minor_radius,
        major_segments=major_segments,
        minor_segments=minor_segments
    )
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    return obj

def add_bmesh_plane(name: str = "Plane",
                    size: float = 1.0,
                    location=(0.0, 0.0, 0.0),
                    rotation=(0.0, 0.0, 0.0),
                    scale=(1.0, 1.0, 1.0)) -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_grid(
        bm,
        x_segments=1,
        y_segments=1,
        size=size
    )
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    return obj

def add_mesh_to_scene(mesh: bpy.types.Mesh, name: str = "primitive_obj") -> bpy.types.Object:
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    return obj

def apply_material(obj: bpy.types.Object, material_info: Dict[str, Any]) -> None:
    if not material_info:
        return
    try:
        path = material_info["path"]
        params = material_info.get("params", {})
        *module_parts, func_name = path.split(".")
        module_str = ".".join(module_parts)
        module = __import__(module_str, fromlist=[func_name])
        func = getattr(module, func_name)
    except Exception:
        print(f"WARNING: Could not import material function `{material_info}`. Skipping.")
        return

    try:
        mat = func(**params)
        if mat is None or not hasattr(mat, "name"):
            print(f"WARNING: Material function `{func_name}` did not return a valid material. Skipping.")
            return
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
    except Exception as e:
        print(f"WARNING: Failed to create/apply material via `{func_name}`: {e}")

def main():
    # Expect: blender --background --python generate_blend_from_json.py -- /path/to/specs.json
    if "--" not in sys.argv:
        print("USAGE ERROR: call as:")
        print("  blender --background --python generate_blend_from_json.py -- /path/to/specs.json")
        sys.exit(1)

    try:
        idx = sys.argv.index("--")
        json_path = Path(sys.argv[idx + 1])
    except Exception:
        print("USAGE ERROR: Could not parse JSON path after `--`.")
        sys.exit(1)

    if not json_path.exists():
        print(f"ERROR: JSON file not found at `{json_path}`")
        sys.exit(1)

    try:
        specs = json.loads(json_path.read_text())
    except Exception:
        print(f"ERROR: Failed to parse JSON `{json_path}`:\n{traceback.format_exc()}")
        sys.exit(1)

    if not isinstance(specs, list):
        print(f"ERROR: Expected top-level JSON array, but got {type(specs)}. Contents:")
        print(json.dumps(specs, indent=2))
        sys.exit(1)

    print(f"✓ Loaded {len(specs)} component(s) from `{json_path}`")

    for i, spec in enumerate(specs):
        if not isinstance(spec, dict):
            print(f"ERROR: Spec #{i} is not a dict: {spec}")
            sys.exit(1)
        if "operations" not in spec or not isinstance(spec["operations"], list):
            print(f"ERROR: Spec #{i} missing `'operations'` list: {spec}")
            sys.exit(1)

    try:
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()
        print("✓ Cleared existing objects from the scene.")
    except Exception:
        print("ERROR: Could not delete existing objects:\n", traceback.format_exc())
        sys.exit(1)

    for comp_idx, spec in enumerate(specs):
        comp_name = spec.get("name", f"Component_{comp_idx}")
        ops = spec["operations"]
        last_obj = None

        print(f"→ Processing component #{comp_idx}: '{comp_name}' with {len(ops)} operation(s).")

        for op_idx, op_spec in enumerate(ops):
            try:
                op_name = op_spec["operation"]
                raw_params = op_spec.get("params", {}) or {}
                raw_transform = op_spec.get("transform", {}) or {}

                # Extract transform fields (with defaults)
                location = tuple(raw_transform.get("location", (0.0, 0.0, 0.0)))
                rotation = tuple(raw_transform.get("rotation", (0.0, 0.0, 0.0)))
                scale    = tuple(raw_transform.get("scale",    (1.0, 1.0, 1.0)))

                # Decide which primitive to create, using BMesh helpers
                if op_name == "bpy.ops.mesh.primitive_cube_add":
                    size = float(raw_params.get("size", 1.0))
                    last_obj = add_bmesh_cube(
                        name=f"{comp_name}_{comp_idx}_{op_idx}_Cube",
                        size=size,
                        location=location,
                        rotation=rotation,
                        scale=scale
                    )

                elif op_name == "bpy.ops.mesh.primitive_cylinder_add":
                    radius = float(raw_params.get("radius", 1.0))
                    depth  = float(raw_params.get("depth", 2.0))
                    verts  = int(raw_params.get("vertices", 32))
                    last_obj = add_bmesh_cylinder(
                        name=f"{comp_name}_{comp_idx}_{op_idx}_Cylinder",
                        radius=radius,
                        depth=depth,
                        location=location,
                        rotation=rotation,
                        scale=scale,
                        verts=verts
                    )

                elif op_name == "bpy.ops.mesh.primitive_uv_sphere_add":
                    radius   = float(raw_params.get("radius", 1.0))
                    segments = int(raw_params.get("segments", 32))
                    rings    = int(raw_params.get("rings", 16))
                    last_obj = add_bmesh_uv_sphere(
                        name=f"{comp_name}_{comp_idx}_{op_idx}_UVSphere",
                        radius=radius,
                        location=location,
                        rotation=rotation,
                        scale=scale,
                        segments=segments,
                        rings=rings
                    )

                elif op_name == "bpy.ops.mesh.primitive_cone_add":
                    radius1  = float(raw_params.get("radius1", 1.0))
                    radius2  = float(raw_params.get("radius2", 0.0))
                    depth    = float(raw_params.get("depth", 2.0))
                    segments = int(raw_params.get("vertices", 32))
                    last_obj = add_bmesh_cone(
                        name=f"{comp_name}_{comp_idx}_{op_idx}_Cone",
                        radius1=radius1,
                        radius2=radius2,
                        depth=depth,
                        location=location,
                        rotation=rotation,
                        scale=scale,
                        segments=segments
                    )

                elif op_name == "bpy.ops.mesh.primitive_torus_add":
                    major_radius   = float(raw_params.get("major_radius", 1.0))
                    minor_radius   = float(raw_params.get("minor_radius", 0.25))
                    major_segments = int(raw_params.get("major_segments", 48))
                    minor_segments = int(raw_params.get("minor_segments", 12))
                    last_obj = add_bmesh_torus(
                        name=f"{comp_name}_{comp_idx}_{op_idx}_Torus",
                        major_radius=major_radius,
                        minor_radius=minor_radius,
                        location=location,
                        rotation=rotation,
                        scale=scale,
                        major_segments=major_segments,
                        minor_segments=minor_segments
                    )

                elif op_name == "bpy.ops.mesh.primitive_plane_add":
                    size = float(raw_params.get("size", 1.0))
                    last_obj = add_bmesh_plane(
                        name=f"{comp_name}_{comp_idx}_{op_idx}_Plane",
                        size=size,
                        location=location,
                        rotation=rotation,
                        scale=scale
                    )

                else:
                    # Not a built-in primitive: try to resolve a custom function
                    if op_name in globals():
                        func = globals()[op_name]
                        result = func(**raw_params)
                        if isinstance(result, bpy.types.Mesh):
                            last_obj = add_mesh_to_scene(result, name=f"{comp_name}_{comp_idx}_{op_idx}")
                            # Apply transform
                            last_obj.location = location
                            last_obj.rotation_euler = rotation
                            last_obj.scale = scale
                        elif isinstance(result, bpy.types.Object):
                            last_obj = result
                            last_obj.location = location
                            last_obj.rotation_euler = rotation
                            last_obj.scale = scale
                        else:
                            print(f"WARNING: `{op_name}` returned unexpected type {type(result)}; skipping.")
                            continue

                    elif draw_utils is not None and hasattr(draw_utils, op_name):
                        func = getattr(draw_utils, op_name)
                        result = func(**raw_params)
                        if isinstance(result, bpy.types.Mesh):
                            last_obj = add_mesh_to_scene(result, name=f"{comp_name}_{comp_idx}_{op_idx}")
                            last_obj.location = location
                            last_obj.rotation_euler = rotation
                            last_obj.scale = scale
                        elif isinstance(result, bpy.types.Object):
                            last_obj = result
                            last_obj.location = location
                            last_obj.rotation_euler = rotation
                            last_obj.scale = scale
                        else:
                            print(f"WARNING: draw_utils.`{op_name}` returned unexpected type {type(result)}; skipping.")
                            continue

                    else:
                        print(f"ERROR: Unknown operation `{op_name}` in component '{comp_name}'.")
                        sys.exit(1)

                if last_obj is None:
                    print(f"WARNING: Operation `{op_name}` did not create an object. Continuing.")
                    continue

                print(f"   ✓ Created `{last_obj.name}` via `{op_name}`")

                # If the spec had a material field at the component level, apply it now
                if "material" in spec:
                    apply_material(last_obj, spec["material"])

            except TypeError as te:
                print(f"ERROR: TypeError running `{op_name}` with params {raw_params}:\n{te}")
                sys.exit(1)
            except Exception:
                print(f"ERROR: Exception during `{op_name}`:\n{traceback.format_exc()}")
                sys.exit(1)

    # ─── Save the resulting .blend file next to the JSON ───────────────────────────────────────
    blend_path = json_path.with_suffix(".blend")
    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
        print(f"✓ Saved .blend to `{blend_path}`")
    except Exception:
        print(f"ERROR: Could not save .blend at `{blend_path}`:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
