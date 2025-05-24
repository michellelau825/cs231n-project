import sys
import os
from pathlib import Path
import traceback

# Get the project root directory
project_root = Path(__file__).parent.parent

# Add project root to Python path
sys.path.append(str(project_root))

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

import json
import bpy
import numpy as np
from infinigen.core.util import blender as butil

try:
    import scipy
except ImportError:
    pass

# Import draw utilities after fixing Python path
from infinigen.assets.utils import draw as draw_utils

# Simple linear interpolation function to replace scipy.interpolate.interp1d
def linear_interp(x, xp, fp):
    """Simple linear interpolation function"""
    return np.interp(x, xp, fp)

# Simplified mesh utilities without shapely dependency
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

def bezier_curve(anchors, vector_locations=(), resolution=None, to_mesh=True):
    """Create a bezier curve from anchor points"""
    n = len(anchors[0])
    anchors = np.array([
        np.array(r, dtype=float) if isinstance(r, (list, tuple)) else np.full(n, r)
        for r in anchors
    ])
    
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    obj = bpy.context.active_object

    if n > 2:
        with butil.ViewportMode(obj, "EDIT"):
            bpy.ops.curve.subdivide(number_cuts=n - 2)
    points = obj.data.splines[0].bezier_points
    for i in range(n):
        points[i].co = anchors[:, i]
    for i in range(n):
        if i in vector_locations:
            points[i].handle_left_type = "VECTOR"
            points[i].handle_right_type = "VECTOR"
        else:
            points[i].handle_left_type = "AUTO"
            points[i].handle_right_type = "AUTO"
    obj.data.splines[0].resolution_u = resolution if resolution is not None else 12
    if not to_mesh:
        return obj
    return curve2mesh(obj)

def curve2mesh(obj):
    """Convert a curve to a mesh"""
    points = obj.data.splines[0].bezier_points
    cos = np.array([p.co for p in points])
    length = np.linalg.norm(cos[:-1] - cos[1:], axis=-1)
    min_length = 5e-3
    with butil.ViewportMode(obj, "EDIT"):
        for i in range(len(points)):
            if points[i].handle_left_type == "FREE":
                points[i].handle_left_type = "ALIGNED"
            if points[i].handle_right_type == "FREE":
                points[i].handle_right_type = "ALIGNED"
        for i in reversed(range(len(points) - 1)):
            points = list(obj.data.splines[0].bezier_points)
            number_cuts = min(int(length[i] / min_length) - 1, 64)
            if number_cuts < 0:
                continue
            bpy.ops.curve.select_all(action="DESELECT")
            points[i].select_control_point = True
            points[i + 1].select_control_point = True
            bpy.ops.curve.subdivide(number_cuts=number_cuts)
    obj.data.splines[0].resolution_u = 1
    with butil.SelectObjects(obj):
        bpy.ops.object.convert(target="MESH")
    obj = bpy.context.active_object
    butil.modify_mesh(obj, "WELD", merge_threshold=1e-3)
    return obj

def align_bezier(anchors, axes=None, scale=None, vector_locations=(), resolution=None, to_mesh=True):
    """Create an aligned bezier curve"""
    obj = bezier_curve(anchors, vector_locations, resolution, False)
    points = obj.data.splines[0].bezier_points
    if scale is None:
        scale = np.ones(2 * len(points) - 2)
    if axes is None:
        axes = [None] * len(points)
    scale = [1, *scale, 1]
    for i, p in enumerate(points):
        a = axes[i]
        if a is None:
            continue
        a = np.array(a)
        p.handle_left_type = "FREE"
        p.handle_right_type = "FREE"
        proj_left = np.array(p.handle_left - p.co) @ a * a
        p.handle_left = (
            np.array(p.co)
            + proj_left
            / np.linalg.norm(proj_left)
            * np.linalg.norm(p.handle_left - p.co)
            * scale[2 * i]
        )
        proj_right = np.array(p.handle_right - p.co) @ a * a
        p.handle_right = (
            np.array(p.co)
            + proj_right
            / np.linalg.norm(proj_right)
            * np.linalg.norm(p.handle_right - p.co)
            * scale[2 * i + 1]
        )
    if not to_mesh:
        return obj
    return curve2mesh(obj)

def add_mesh_to_scene(mesh, name="primitive_obj"):
    """Add a mesh to the Blender scene as an object"""
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj

def get_operation_function(op_name):
    """Get the function for an operation, handling module prefixes"""
    # Remove module prefix if present
    if '.' in op_name:
        module_name, func_name = op_name.rsplit('.', 1)
    else:
        func_name = op_name

    # Try to get the function from globals first
    if func_name in globals():
        return globals()[func_name]
    
    # Try to get from draw_utils
    if hasattr(draw_utils, func_name):
        return getattr(draw_utils, func_name)
    
    # Try to get from bpy.ops
    if op_name.startswith('bpy.ops.'):
        parts = op_name.split('.')
        op = bpy.ops
        for part in parts[1:]:
            op = getattr(op, part)
        return op
    
    raise ValueError(f"Unknown operation: {op_name}")

def apply_transform(obj, transform):
    """Apply transformation to an object"""
    if 'location' in transform:
        obj.location = transform['location']
    if 'rotation' in transform:
        obj.rotation_euler = transform['rotation']
    if 'scale' in transform:
        obj.scale = transform['scale']

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
    if len(sys.argv) < 2:
        sys.exit(1)
        
    try:
        idx = sys.argv.index("--")
        json_path = sys.argv[idx + 1]
    except (ValueError, IndexError):
        sys.exit(1)

    try:
        with open(json_path, "r") as f:
            specs = json.load(f)
    except Exception:
        sys.exit(1)

    # Clear existing objects
    try:
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
    except Exception:
        sys.exit(1)

    for i, spec in enumerate(specs):
        for j, op_spec in enumerate(spec.get('operations', [])):
            try:
                op_func = get_operation_function(op_spec['operation'])
                
                # Call the operation function
                result = op_func(**op_spec.get('params', {}))
                
                # Handle the result
                if isinstance(result, bpy.types.Mesh):
                    obj = add_mesh_to_scene(result, name=f"{spec.get('name', 'Component')}_{i}_{j}")
                elif isinstance(result, bpy.types.Object):
                    obj = result
                else:
                    continue
                
                # Apply transformations
                if 'transform' in op_spec:
                    try:
                        apply_transform(obj, op_spec['transform'])
                    except Exception:
                        continue
                
            except Exception:
                continue
        
        # Apply material to the last created object
        if 'material' in spec:
            try:
                apply_material(obj, spec['material'])
            except Exception:
                pass

    # Save the result
    try:
        blend_path = Path(json_path).with_suffix('.blend')
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main() 