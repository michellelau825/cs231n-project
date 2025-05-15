import bpy
import math
import os
from pathlib import Path

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
    
    # Create table top
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, height/2)
    )
    table = bpy.context.active_object
    table.scale = (width, depth, thickness)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    # Create table legs
    leg_height = height - thickness
    leg_positions = [
        (width/2 - 0.05, depth/2 - 0.05),
        (width/2 - 0.05, -depth/2 + 0.05),
        (-width/2 + 0.05, depth/2 - 0.05),
        (-width/2 + 0.05, -depth/2 + 0.05)
    ]
    
    for x, y in leg_positions:
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.03,
            depth=leg_height,
            location=(x, y, leg_height/2)
        )
        leg = bpy.context.active_object
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

def create_dining_chair(position, rotation=0):
    """Create a dining chair with standard measurements"""
    # Convert cm to meters
    width = 0.45  # 45cm
    depth = 0.45  # 45cm
    height = 0.9  # 90cm
    thickness = 0.05  # 5cm
    back_height = 0.45  # 45cm
    
    # Create chair seat
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(position[0], position[1], height/2)
    )
    chair = bpy.context.active_object
    chair.scale = (width, depth, thickness)
    chair.rotation_euler[2] = math.radians(rotation)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    # Create chair back
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(
            position[0],
            position[1] + depth/2 * math.cos(math.radians(rotation)),
            height + back_height/2
        )
    )
    back = bpy.context.active_object
    back.scale = (width, thickness, back_height)
    back.rotation_euler[2] = math.radians(rotation)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    # Join seat and back
    bpy.ops.object.select_all(action='DESELECT')
    chair.select_set(True)
    back.select_set(True)
    bpy.context.view_layer.objects.active = chair
    bpy.ops.object.join()
    
    # Create chair legs
    leg_height = height - thickness
    leg_positions = [
        (width/2 - 0.02, depth/2 - 0.02),
        (width/2 - 0.02, -depth/2 + 0.02),
        (-width/2 + 0.02, depth/2 - 0.02),
        (-width/2 + 0.02, -depth/2 + 0.02)
    ]
    
    for x, y in leg_positions:
        # Rotate leg positions
        rx = x * math.cos(math.radians(rotation)) - y * math.sin(math.radians(rotation))
        ry = x * math.sin(math.radians(rotation)) + y * math.cos(math.radians(rotation))
        
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.02,
            depth=leg_height,
            location=(
                position[0] + rx,
                position[1] + ry,
                leg_height/2
            )
        )
        leg = bpy.context.active_object
        leg.rotation_euler[2] = math.radians(rotation)
        bpy.ops.object.select_all(action='DESELECT')
        chair.select_set(True)
        leg.select_set(True)
        bpy.context.view_layer.objects.active = chair
        bpy.ops.object.join()
    
    # Apply wood material
    material = bpy.data.materials.new(name="chair_material")
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.4, 0.2, 0.1, 1)  # Dark wood color
    bsdf.inputs["Roughness"].default_value = 0.7
    chair.data.materials.append(material)
    
    return chair

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