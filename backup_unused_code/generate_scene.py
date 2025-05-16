import bpy
import math
import os
from pathlib import Path
import sys
import numpy as np

# Add the infinigen root to Python path
infinigen_root = Path(__file__).parent.parent
sys.path.append(str(infinigen_root))

from infinigen.assets.utils.draw import spin, bezier_curve, leaf
from infinigen.assets.utils.decorate import displace_vertices
from infinigen.assets.utils.object import new_bbox, new_icosphere, new_circle
from infinigen.assets.utils.geometry.nurbs import blender_nurbs
from infinigen.assets.utils.geometry.lofting import loft
from infinigen.assets.utils.mesh import build_prism_mesh
from infinigen.core.util import blender as butil
from .furniture_analyzer import FurnitureAnalyzer
from .llm_client import LLMClient

def clear_scene():
    """Clear existing scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def create_dining_table():
    """Create a dining table with standard measurements"""
    # Convert cm to meters
    width = 1.8  # 180cm
    depth = 0.9  # 90cm
    height = 0.75  # 75cm
    thickness = 0.05  # 5cm
    
    # Create table top using bbox primitive
    table = new_bbox(-width/2, width/2, -depth/2, depth/2, height - thickness, height)
    
    # Create table legs using prism mesh
    leg_height = height - thickness
    leg_positions = [
        (width/2 - 0.05, depth/2 - 0.05),
        (width/2 - 0.05, -depth/2 + 0.05),
        (-width/2 + 0.05, depth/2 - 0.05),
        (-width/2 + 0.05, -depth/2 + 0.05)
    ]
    
    for x, y in leg_positions:
        # Create leg using prism mesh
        leg_mesh = build_prism_mesh(n=8, r_min=0.02, r_max=0.03, height=0.02, tilt=0.1)
        leg = bpy.data.objects.new("leg", leg_mesh)
        bpy.context.scene.collection.objects.link(leg)
        leg.location = (x, y, leg_height/2)
        leg.scale = (1, 1, leg_height)
        butil.apply_transform(leg)
        
        # Join with table
        bpy.ops.object.select_all(action='DESELECT')
        table.select_set(True)
        leg.select_set(True)
        bpy.context.view_layer.objects.active = table
        bpy.ops.object.join()
    
    # Apply wood material
    material = bpy.data.materials.new(name="table_material")
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.4, 0.2, 0.1, 1)  # Dark wood color
    bsdf.inputs["Roughness"].default_value = 0.7
    table.data.materials.append(material)
    
    return table

def create_dining_chair(position, rotation=0, style="modern"):
    """Create a dining chair with realistic structure"""
    # Base measurements (in meters)
    width = 0.45  # 45cm
    depth = 0.45  # 45cm
    height = 0.9  # 90cm
    thickness = 0.05  # 5cm
    back_height = 0.45  # 45cm
    
    # Create chair seat using bbox primitive
    seat = new_bbox(-width/2, width/2, -depth/2, depth/2, height - thickness, height)
    seat.rotation_euler[2] = math.radians(rotation)
    seat.location = position
    butil.apply_transform(seat)
    
    # Create chair back using bezier curve
    back_anchors = [
        [0, 0, 0],
        [0, 0.1, 0.1],  # Slight curve
        [0, 0, back_height]
    ]
    back = bezier_curve(back_anchors, resolution=12)
    back.scale = (width, 1, 1)
    back.location = (
        position[0],
        position[1] + depth/2 * math.cos(math.radians(rotation)),
        height
    )
    back.rotation_euler[2] = math.radians(rotation)
    
    # Create chair legs using prism mesh
    leg_height = height - thickness
    leg_positions = [
        (width/2 - 0.02, depth/2 - 0.02),
        (width/2 - 0.02, -depth/2 + 0.02),
        (-width/2 + 0.02, depth/2 - 0.02),
        (-width/2 + 0.02, -depth/2 + 0.02)
    ]
    
    legs = []
    for x, y in leg_positions:
        # Rotate leg positions
        rx = x * math.cos(math.radians(rotation)) - y * math.sin(math.radians(rotation))
        ry = x * math.sin(math.radians(rotation)) + y * math.cos(math.radians(rotation))
        
        # Create leg using prism mesh
        leg_mesh = build_prism_mesh(n=8, r_min=0.015, r_max=0.02, height=0.01, tilt=0.05)
        leg = bpy.data.objects.new("leg", leg_mesh)
        bpy.context.scene.collection.objects.link(leg)
        leg.location = (
            position[0] + rx,
            position[1] + ry,
            leg_height/2
        )
        leg.scale = (1, 1, leg_height)
        leg.rotation_euler[2] = math.radians(rotation)
        butil.apply_transform(leg)
        legs.append(leg)
    
    # Add support structure using bezier curves
    support_anchors = [
        [width/2 - 0.02, depth/2 - 0.02, height - thickness],
        [width/2 - 0.02, -depth/2 + 0.02, height - thickness],
        [-width/2 + 0.02, depth/2 - 0.02, height - thickness],
        [-width/2 + 0.02, -depth/2 + 0.02, height - thickness]
    ]
    
    # Create support rails
    for i in range(4):
        start = support_anchors[i]
        end = support_anchors[(i + 1) % 4]
        rail_anchors = [
            [start[0], start[1], start[2]],
            [(start[0] + end[0])/2, (start[1] + end[1])/2, start[2]],
            [end[0], end[1], end[2]]
        ]
        rail = bezier_curve(rail_anchors, resolution=8)
        rail.scale = (1, 1, 0.02)  # Thin rail
        rail.rotation_euler[2] = math.radians(rotation)
        rail.location = (position[0], position[1], 0)
    
    # Join all components
    bpy.ops.object.select_all(action='DESELECT')
    seat.select_set(True)
    back.select_set(True)
    for leg in legs:
        leg.select_set(True)
    bpy.context.view_layer.objects.active = seat
    bpy.ops.object.join()
    
    # Apply wood material
    material = bpy.data.materials.new(name="chair_material")
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.4, 0.2, 0.1, 1)  # Dark wood color
    bsdf.inputs["Roughness"].default_value = 0.7
    seat.data.materials.append(material)
    
    return seat

def generate_scene():
    """Generate a complete dining room scene"""
    # Clear existing scene
    clear_scene()
    
    # Create table
    table = create_dining_table()
    
    # Create chairs
    chair_positions = [
        ((0, -1.2), 0),      # Front
        ((0, 1.2), 180),     # Back
        ((-1.2, 0), 90),     # Left
        ((1.2, 0), -90)      # Right
    ]
    
    for pos, rot in chair_positions:
        create_dining_chair(pos, rot)
    
    # Save the scene
    output_dir = Path(os.path.expanduser("~/Desktop/generated-assets"))
    output_dir.mkdir(exist_ok=True)
    
    # Save as .blend file
    blend_path = output_dir / "dining_room_scene.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    
    print(f"Scene saved to: {blend_path}")

if __name__ == "__main__":
    generate_scene() 