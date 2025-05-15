import os
import argparse
from pathlib import Path
import bpy
from infinigen.primitive_builder.primitive_builder import ProceduralSceneBuilder
from infinigen.primitive_builder.llm_client import LLMClient
from infinigen.core.util import blender as butil
from infinigen.core import init

def setup_renderer():
    """Set up Cycles renderer with GPU acceleration"""
    # Set render engine to Cycles
    bpy.context.scene.render.engine = 'CYCLES'
    
    # Configure Cycles settings
    bpy.context.scene.cycles.device = 'GPU'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.cycles.use_denoising = True
    
    # Configure output settings
    bpy.context.scene.render.resolution_x = 512
    bpy.context.scene.render.resolution_y = 512
    bpy.context.scene.render.resolution_percentage = 100
    
    # Configure Cycles devices
    init.configure_cycles_devices()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("description", type=str, help="Description of the object to create")
    parser.add_argument("--output-dir", type=str, default="generated_assets", help="Output directory")
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Initialize LLM client
    llm_client = LLMClient()
    
    # Create scene builder
    builder = ProceduralSceneBuilder(llm_client)
    
    # Build object from description
    obj = builder.build_from_description(args.description)
    
    # Add a simple camera
    bpy.ops.object.camera_add(location=(0, -5, 2))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.0, 0, 0)
    bpy.context.scene.camera = camera
    
    # Add light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 5))
    light = bpy.context.active_object
    light.data.energy = 5.0
    
    # Set up renderer
    setup_renderer()
    
    # Save blend file
    blend_path = output_dir / "scene.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    
    # Set output path and render
    bpy.context.scene.render.filepath = str(output_dir / "render.png")
    bpy.ops.render.render(write_still=True)
    
    print(f"Created object and saved to {output_dir}")
    print(f"Blender file: {blend_path}")
    print(f"Render: {output_dir / 'render.png'}")

if __name__ == "__main__":
    main() 