import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bpy
from infinigen.nl_interface.nl_interface import InfinigenNLInterface
from infinigen.core.util import blender as butil

def setup_scene():
    """Set up a basic scene for rendering"""
    # Clear existing scene
    butil.clear_scene()
    
    # Add a light
    bpy.ops.object.light_add(type='SUN')
    light = bpy.context.active_object
    light.rotation_euler = (-0.7, 0.1, 0.22)
    light.data.energy = 5
    
    # Add a ground plane
    bpy.ops.mesh.primitive_plane_add(size=10)
    ground = bpy.context.active_object
    ground.location.z = -0.1
    
    # Set up camera
    bpy.ops.object.camera_add()
    camera = bpy.context.active_object
    camera.location = (3, -3, 2)
    camera.rotation_euler = (1.0, 0, 0.8)
    bpy.context.scene.camera = camera
    
    # Set up render settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_x = 800
    bpy.context.scene.render.resolution_y = 600
    bpy.context.scene.render.film_transparent = True

def main():
    # Initialize the interface
    nl_interface = InfinigenNLInterface()
    
    # Set up the scene
    setup_scene()
    
    # Example prompts
    prompts = [
        "Create a modern wooden chair with adjustable height",
        "Generate a minimalist glass coffee table",
        "Design a traditional wooden dining table"
    ]
    
    # Create output directory
    output_dir = "generated_assets"
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each prompt
    for i, prompt in enumerate(prompts):
        print(f"\nProcessing: {prompt}")
        try:
            # Generate asset
            result = nl_interface.generate_asset(prompt)
            
            # Print results
            print(f"Generated {result['type']} with:")
            print(f"- Style: {result['style']}")
            print(f"- Materials: {', '.join(result['materials'])}")
            print(f"- Size: {result['size']}")
            
            # Position the object
            obj = result['object']
            obj.location = (0, 0, 0)
            
            # Set output paths
            blend_path = os.path.join(output_dir, f"{result['type']}_{i}.blend")
            render_path = os.path.join(output_dir, f"{result['type']}_{i}.png")
            
            # Save the blend file
            bpy.ops.wm.save_as_mainfile(filepath=blend_path)
            
            # Render the asset
            bpy.context.scene.render.filepath = render_path
            bpy.ops.render.render(write_still=True)
            
            print(f"Saved blend file to: {blend_path}")
            print(f"Saved render to: {render_path}")
            
            # Clear the scene for the next asset
            if i < len(prompts) - 1:
                setup_scene()
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

if __name__ == "__main__":
    main() 