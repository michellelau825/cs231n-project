import bpy
import sys
from pathlib import Path
import openai

# Add the infinigen root to Python path
infinigen_root = Path(__file__).parent.parent
sys.path.append(str(infinigen_root))

from infinigen.assets.utils.draw import bezier_curve, build_prism_mesh
from infinigen.core.util import blender as butil

def get_primitive_specs(prompt: str) -> list:
    """Use GPT-4 to convert prompt to primitive specifications"""
    client = openai.OpenAI()
    
    system_prompt = """You are a 3D modeling expert. Convert the following description into a series of primitive operations.
    Available operations:
    - build_prism_mesh: Creates prismatic mesh. Parameters: n (sides), r_min, r_max, height
    - bezier_curve: Creates a curved shape. Parameters: anchors (list of [x,y,z] points), resolution
    
    Respond with a JSON array of operations, each containing:
    - operation: one of the available operations
    - params: parameters for the operation
    - transform: optional transformation parameters (location, rotation, scale)
    
    Example response format:
    [
        {
            "operation": "build_prism_mesh",
            "params": {"n": 4, "r_min": 0.25, "r_max": 0.25, "height": 0.05},
            "transform": {"location": [0, 0, 0.45]}
        }
    ]
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        specs = eval(response.choices[0].message.content)
        print("Generated specifications:", specs)
        return specs
        
    except Exception as e:
        print(f"Error generating specifications: {e}")
        return [{
            "operation": "build_prism_mesh",
            "params": {"n": 4, "r_min": 0.5, "r_max": 0.5, "height": 0.1},
            "transform": {"location": [0, 0, 0]}
        }]

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

def main():
    # Get the prompt from command line arguments
    if len(sys.argv) < 2:
        print("Usage: blender --background --python create_object.py \"Your object description\"")
        return
    
    # Find the index of the "--" separator
    try:
        separator_index = sys.argv.index("--")
        prompt = " ".join(sys.argv[separator_index + 1:])
    except ValueError:
        print("Error: No prompt provided after '--' separator")
        return
    
    # Clear existing scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Get the prompt and create object
    specs = get_primitive_specs(prompt)
    object = create_from_primitives(specs)
    
    # Save the result
    output_path = Path("~/Desktop/generated-objects").expanduser()
    output_path.mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path / "generated_object.blend"))
    print(f"Object saved to: {output_path / 'generated_object.blend'}")

if __name__ == "__main__":
    main() 