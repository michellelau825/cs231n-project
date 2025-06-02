#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import json
import traceback
from typing import Any, Dict

# Get the project root directory (cs231n-project)
project_root = Path(__file__).parent.parent.parent

# Add project root to Python path
sys.path.insert(0, str(project_root))

# Add conda environment site-packages
conda_env = os.getenv('CONDA_PREFIX')
if conda_env:
    site_packages = Path(conda_env) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
    if site_packages.exists():
        sys.path.append(str(site_packages))

# Add user site-packages
user_site = Path.home() / '.local' / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
if user_site.exists():
    sys.path.append(str(user_site))

# Attempt imports, fail loudly if missing
try:
    import bpy
except Exception as e:
    print("ERROR: Could not import `bpy`. Make sure you are running this inside Blender.")
    raise

try:
    import numpy as np
except Exception as e:
    print("ERROR: Could not import `numpy`. You need to install it into Blender's Python environment.")
    raise

# Try to import infinigen utilities (if your pipeline needs them). If it fails, we'll warn but continue.
butil = None
draw_utils = None
try:
    # Add infinigen package to path
    infinigen_path = project_root / "infinigen"
    if infinigen_path.exists():
        sys.path.insert(0, str(infinigen_path))
    
    from infinigen.core.util import blender as butil
    from infinigen.assets.utils import draw as draw_utils
except ModuleNotFoundError as e:
    print(f"WARNING: Could not import parts of `infinigen`: {e}")
    print("Current sys.path:")
    for p in sys.path:
        print(f"  - {p}")
    print("WARNING: If you rely on those functions inside primitives, you will error later.")
    # We do NOT sys.exit here, because maybe you aren't actually using those imports in your JSON.

def linear_interp(x, xp, fp):
    """Simple linear interpolation function"""
    return np.interp(x, xp, fp)

def build_prism_mesh(n=6, r_min=1.0, r_max=1.5, height=0.3, tilt=0.3):
    """Create a prism mesh with n sides"""
    angles = np.linspace(0, 2*np.pi, n, endpoint=False)
    r_upper = np.random.uniform(r_min, r_max, n)
    r_lower = np.random.uniform(r_min, r_max, n)
    z_upper = height + tilt * np.cos(angles)
    z_lower = -height + tilt * np.sin(angles)

    vertices = []
    for i in range(n):
        angle = angles[i]
        # Upper vertices
        vertices.append((r_upper[i] * np.cos(angle), r_upper[i] * np.sin(angle), z_upper[i]))
        # Lower vertices
        vertices.append((r_lower[i] * np.cos(angle), r_lower[i] * np.sin(angle), z_lower[i]))

    faces = []
    for i in range(n):
        next_i = (i + 1) % n
        # Side faces
        faces.append([i*2, next_i*2, next_i*2+1, i*2+1])
        # Top face
        faces.append([i*2 for i in range(n)])
        # Bottom face
        faces.append([i*2+1 for i in range(n)])

    mesh = bpy.data.meshes.new("prism")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return mesh

def build_cylinder_mesh(radius=1.0, height=2.0, segments=32):
    """Create a cylinder mesh"""
    angles = np.linspace(0, 2*np.pi, segments, endpoint=False)
    vertices = []
    for angle in angles:
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        vertices.append((x, y, -height/2))
        vertices.append((x, y, height/2))

    faces = []
    for i in range(segments):
        next_i = (i + 1) % segments
        # Side faces
        faces.append([i*2, next_i*2, next_i*2+1, i*2+1])
        # Top face
        faces.append([i*2+1 for i in range(segments)])
        # Bottom face
        faces.append([i*2 for i in range(segments)])

    mesh = bpy.data.meshes.new("cylinder")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return mesh

def build_box_mesh(width=1.0, depth=1.0, height=1.0):
    """Create a box mesh"""
    w, d, h = width/2, depth/2, height/2
    vertices = [
        (-w, -d, -h), (w, -d, -h), (w, d, -h), (-w, d, -h),
        (-w, -d, h), (w, -d, h), (w, d, h), (-w, d, h)
    ]
    faces = [
        [0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
        [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4]
    ]
    mesh = bpy.data.meshes.new("box")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return mesh

def build_plane_mesh(width=1.0, depth=1.0):
    """Create a plane mesh"""
    w, d = width/2, depth/2
    vertices = [(-w, -d, 0), (w, -d, 0), (w, d, 0), (-w, d, 0)]
    faces = [[0, 1, 2, 3]]
    mesh = bpy.data.meshes.new("plane")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return mesh

def build_sphere_mesh(radius=1.0, segments=32, rings=16):
    """Create a sphere mesh"""
    # Create a UV sphere using Blender's built-in operator
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius,
        segments=segments,
        ring_count=rings
    )
    # Get the created mesh
    sphere = bpy.context.active_object.data
    # Create a new mesh to return
    mesh = bpy.data.meshes.new("sphere")
    # Copy the sphere data to our new mesh
    vertices = [v.co[:] for v in sphere.vertices]
    faces = [[v for v in p.vertices] for p in sphere.polygons]
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    # Delete the temporary sphere object
    bpy.data.objects.remove(bpy.context.active_object)
    return mesh

def build_cone_mesh(radius=1.0, height=2.0, segments=32):
    """Create a cone mesh"""
    # Create a cone using Blender's built-in operator
    bpy.ops.mesh.primitive_cone_add(
        radius1=radius,
        radius2=0,
        depth=height,
        vertices=segments
    )
    # Get the created mesh
    cone = bpy.context.active_object.data
    # Create a new mesh to return
    mesh = bpy.data.meshes.new("cone")
    # Copy the cone data to our new mesh
    vertices = [v.co[:] for v in cone.vertices]
    faces = [[v for v in p.vertices] for p in cone.polygons]
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    # Delete the temporary cone object
    bpy.data.objects.remove(bpy.context.active_object)
    return mesh

def build_torus_mesh(major_radius=1.0, minor_radius=0.3, major_segments=32, minor_segments=16):
    """Create a torus mesh"""
    # Create a torus using Blender's built-in operator
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=major_segments,
        minor_segments=minor_segments
    )
    # Get the created mesh
    torus = bpy.context.active_object.data
    # Create a new mesh to return
    mesh = bpy.data.meshes.new("torus")
    # Copy the torus data to our new mesh
    vertices = [v.co[:] for v in torus.vertices]
    faces = [[v for v in p.vertices] for p in torus.polygons]
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    # Delete the temporary torus object
    bpy.data.objects.remove(bpy.context.active_object)
    return mesh

def get_operation_function(op_name):
    """Get the function for an operation, handling module prefixes"""
    # Handle Blender operators
    if op_name.startswith('bpy.ops.'):
        # Map primitive operators to their correct Blender API calls
        if op_name == "bpy.ops.mesh.primitive_cube_add":
            return lambda **kwargs: bpy.ops.mesh.primitive_cube_add(**kwargs)
        elif op_name == "bpy.ops.mesh.primitive_cylinder_add":
            return lambda **kwargs: bpy.ops.mesh.primitive_cylinder_add(**kwargs)
        elif op_name == "bpy.ops.mesh.primitive_uv_sphere_add":
            return lambda **kwargs: bpy.ops.mesh.primitive_uv_sphere_add(**kwargs)
        elif op_name == "bpy.ops.mesh.primitive_cone_add":
            return lambda **kwargs: bpy.ops.mesh.primitive_cone_add(**kwargs)
        elif op_name == "bpy.ops.mesh.primitive_torus_add":
            return lambda **kwargs: bpy.ops.mesh.primitive_torus_add(**kwargs)
        elif op_name == "bpy.ops.mesh.primitive_plane_add":
            return lambda **kwargs: bpy.ops.mesh.primitive_plane_add(**kwargs)
        else:
            # For other bpy.ops operators, try to resolve them directly
            parts = op_name.split('.')
            op = bpy.ops
            for p in parts[1:]:
                if not hasattr(op, p):
                    raise ValueError(f"Unknown Blender operator segment `{p}` in `{op_name}`")
                op = getattr(op, p)
            return op

    # Try to get the function from globals first
    if op_name in globals():
        return globals()[op_name]
    
    # Try to get from draw_utils
    if hasattr(draw_utils, op_name):
        return getattr(draw_utils, op_name)
    
    raise ValueError(f"Unknown operation: {op_name}")

def apply_transform(obj, transform):
    """Apply transformation to an object"""
    if 'location' in transform:
        obj.location = transform['location']
    if 'rotation' in transform:
        obj.rotation_euler = transform['rotation']
    if 'scale' in transform:
        obj.scale = transform['scale']

def add_mesh_to_scene(mesh, name="primitive_obj"):
    """Add a mesh to the Blender scene as an object"""
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj

def apply_material(obj, material_info):
    """Apply material to an object"""
    if not material_info:
        return

    try:
        # Parse the material path
        *module_parts, function_name = material_info['path'].split('.')
        module_path = '.'.join(module_parts)
        
        # Import the material module
        material_module = __import__(module_path, fromlist=[function_name])
        material_function = getattr(material_module, function_name)
        
        # Create material
        material = material_function(**material_info.get('params', {}))
        
        # Apply to object
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
            
    except Exception:
        pass

def main():
    # The Blender command line is: blender --background --python generate_blend_from_json.py -- /path/to/file.json
    if "--" not in sys.argv:
        print("USAGE ERROR: Should be called as:")
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

    # Load JSON
    try:
        specs = json.loads(json_path.read_text())
    except Exception as e:
        print(f"ERROR: Could not load JSON from `{json_path}`—\n{traceback.format_exc()}")
        sys.exit(1)

    # Confirm that specs is a list
    if not isinstance(specs, list):
        print(f"ERROR: Expected top-level JSON array, but got {type(specs)}. Contents:")
        print(json.dumps(specs, indent=2))
        sys.exit(1)

    print(f"✓ Loaded {len(specs)} component(s) from {json_path}")
    for i, spec in enumerate(specs):
        if not isinstance(spec, dict):
            print(f"ERROR: Spec #{i} is not an object/dict: {spec}")
            sys.exit(1)
        if "operations" not in spec or not isinstance(spec["operations"], list):
            print(f"ERROR: Spec #{i} missing `'operations'` array: {spec}")
            sys.exit(1)

    # Clear existing objects in the scene
    try:
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()
        print("✓ Cleared existing objects from scene.")
    except Exception as e:
        print("ERROR: Could not clear existing objects—\n", traceback.format_exc())
        sys.exit(1)

    # Iterate over each component spec
    for comp_idx, spec in enumerate(specs):
        comp_name = spec.get("name", f"Component_{comp_idx}")
        ops: list = spec["operations"]

        print(f"→ Processing component #{comp_idx}: '{comp_name}' with {len(ops)} operation(s).")

        last_obj = None
        for op_idx, op_spec in enumerate(ops):
            try:
                op_name = op_spec["operation"]
                op_func = get_operation_function(op_name)
            except ValueError as ve:
                print(f"ERROR: Unknown operation `{op_name}` in component '{comp_name}' → {ve}")
                sys.exit(1)

            # Separate params vs. transform
            raw_params = op_spec.get("params", {}) or {}
            raw_transform = op_spec.get("transform", {}) or {}

            # Clean params by removing any transform-related keys
            clean_params = raw_params.copy()
            for key in ["location", "rotation", "scale"]:
                if key in clean_params:
                    del clean_params[key]

            try:
                # Call the operator or custom builder
                if op_name.startswith("bpy.ops."):
                    # For Blender operators, we can pass location and rotation directly
                    op_params = clean_params.copy()
                    if "location" in raw_transform:
                        op_params["location"] = raw_transform["location"]
                    if "rotation" in raw_transform:
                        op_params["rotation"] = raw_transform["rotation"]
                    
                    op_func(**op_params)
                    last_obj = bpy.context.active_object
                else:
                    # For custom mesh builders, only pass mesh-specific params
                    result = op_func(**clean_params)
                    if isinstance(result, bpy.types.Mesh):
                        last_obj = add_mesh_to_scene(result, name=f"{comp_name}_{comp_idx}_{op_idx}")
                    elif isinstance(result, bpy.types.Object):
                        last_obj = result
                    else:
                        print(f"WARNING: Operation `{op_name}` returned unexpected type {type(result)}.")
                        continue

                if last_obj is None:
                    print(f"WARNING: After calling `{op_name}`, `bpy.context.active_object` is None.")
                    continue

                # Apply transform after object creation
                if raw_transform:
                    apply_transform(last_obj, raw_transform)

                print(f"   ✓ Created object `{last_obj.name}` via `{op_name}`.")

            except TypeError as te:
                print(f"ERROR: TypeError when running `{op_name}` with params {clean_params}:\n{te}")
                sys.exit(1)
            except Exception as e:
                print(f"ERROR: Unexpected error during `{op_name}`:\n{traceback.format_exc()}")
                sys.exit(1)

        # Optionally apply material if it exists on the component spec
        if "material" in spec and last_obj is not None:
            try:
                apply_material(last_obj, spec["material"])
                print(f"   ✓ Applied material to `{last_obj.name}`.")
            except Exception as me:
                print(f"WARNING: Failed to apply material on `{comp_name}`: {me}")

    # Save the .blend file
    blend_path = json_path.with_suffix(".blend")
    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
        print(f"✓ Saved .blend to {blend_path}")
    except Exception as e:
        print(f"ERROR: Could not save .blend file to {blend_path}:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
