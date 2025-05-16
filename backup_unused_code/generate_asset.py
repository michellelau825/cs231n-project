import bpy
import json
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from infinigen.assets.utils.draw import build_prism_mesh, bezier_curve
from infinigen.core.util import blender as butil

def clear_scene():
    """Clear existing scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def create_from_primitives(specs: list) -> bpy.types.Object:
    """Create a Blender object from primitive specifications"""
    components = []
    
    for spec in specs:
        op = spec["operation"]
        params = spec["params"]
        transform = spec.get("transform", {})
        
        # Create the base object
        if op == "build_prism_mesh":
            mesh = build_prism_mesh(**params)
            obj = bpy.data.objects.new(f"component_{len(components)}", mesh)
            bpy.context.scene.collection.objects.link(obj)
            
        elif op == "bezier_curve":
            obj = bezier_curve(**params)
        
        # Apply transformations
        if transform:
            if "location" in transform:
                obj.location = transform["location"]
            if "rotation" in transform:
                obj.rotation_euler = transform["rotation"]
            if "scale" in transform:
                obj.scale = transform["scale"]
        
        components.append(obj)
    
    # Join all components
    if components:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in components:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = components[0]
        bpy.ops.object.join()
        return components[0]
    
    return None

def setup_scene():
    """Set up basic scene with camera and lighting"""
    # Add camera
    bpy.ops.object.camera_add(location=(0, -5, 2))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.0, 0, 0)
    bpy.context.scene.camera = camera
    
    # Add light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 5))
    light = bpy.context.active_object
    light.data.energy = 5.0

def main():
    if len(sys.argv) < 2:
        print("Usage: blender --background --python generate_asset.py -- <path_to_primitives.json>")
        sys.exit(1)
    
    # Get the path to primitives.json from command line arguments
    try:
        separator_index = sys.argv.index("--")
        json_path = sys.argv[separator_index + 1]
    except ValueError:
        print("Error: No JSON file path provided after '--' separator")
        sys.exit(1)
    
    # Read primitive specifications
    try:
        with open(json_path, 'r') as f:
            specs = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        sys.exit(1)
    
    # Clear existing scene
    clear_scene()
    
    # Create object from primitives
    obj = create_from_primitives(specs)
    
    # Set up scene
    setup_scene()
    
    # Save the result
    output_path = Path(json_path).parent / "generated_asset.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"Asset saved to: {output_path}")

if __name__ == "__main__":
    main() 