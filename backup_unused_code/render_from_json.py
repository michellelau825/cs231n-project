import bpy
import json
import math
import sys
from pathlib import Path

def clear_scene():
    """Clear existing scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def create_material(name, color, roughness=0.7):
    """Create a procedural material"""
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    return material

def create_table(table_data):
    """Create a table using Blender primitives with proper structure"""
    dims = table_data["dimensions"]
    
    # Create table top with proper thickness and bevel
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, dims["height"] - dims["thickness"]/2)
    )
    table = bpy.context.active_object
    table.scale = (dims["width"], dims["depth"], dims["thickness"])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    # Add bevel to table top edges
    bpy.ops.object.modifier_add(type='BEVEL')
    bevel = table.modifiers["Bevel"]
    bevel.width = dims["thickness"] * 0.1
    bevel.segments = 3
    bpy.ops.object.modifier_apply(modifier="Bevel")
    
    # Create legs with proper structural support
    leg_style = table_data.get("leg_style", "straight")
    leg_positions = [
        (dims["width"]/2 - 0.05, dims["depth"]/2 - 0.05),
        (dims["width"]/2 - 0.05, -dims["depth"]/2 + 0.05),
        (-dims["width"]/2 + 0.05, dims["depth"]/2 - 0.05),
        (-dims["width"]/2 + 0.05, -dims["depth"]/2 + 0.05)
    ]
    
    legs = []
    for pos in leg_positions:
        if leg_style == "straight":
            # Create straight leg with mortise
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=8,
                radius=0.03,
                depth=dims["height"] - dims["thickness"] + 0.03,
                location=(pos[0], pos[1], (dims["height"] - dims["thickness"])/2)
            )
            leg = bpy.context.active_object
            
            # Create mortise in table top
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=8,
                radius=0.032,
                depth=0.03,
                location=(pos[0], pos[1], dims["height"] - dims["thickness"])
            )
            mortise = bpy.context.active_object
            
            # Boolean difference to create mortise
            bool_mod = table.modifiers.new(name="Boolean", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = mortise
            bpy.context.view_layer.objects.active = table
            bpy.ops.object.modifier_apply(modifier="Boolean")
            
            # Delete mortise object
            bpy.data.objects.remove(mortise)
            
        elif leg_style == "single_stand":
            # Create single stand with wider base
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=16,
                radius=0.15,
                depth=dims["height"] - dims["thickness"],
                location=(pos[0], pos[1], (dims["height"] - dims["thickness"])/2)
            )
            leg = bpy.context.active_object
            
            # Taper the stand
            bpy.ops.object.modifier_add(type='SIMPLE_DEFORM')
            deform = leg.modifiers["SimpleDeform"]
            deform.deform_method = 'TAPER'
            deform.factor = 0.3
            bpy.ops.object.modifier_apply(modifier="SimpleDeform")
        
        legs.append(leg)
    
    # Add support structure
    support_height = dims["height"] - dims["thickness"] - 0.1
    for i in range(4):
        start = leg_positions[i]
        end = leg_positions[(i + 1) % 4]
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(
                (start[0] + end[0])/2,
                (start[1] + end[1])/2,
                support_height
            )
        )
        rail = bpy.context.active_object
        length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        rail.scale = (length, 0.03, 0.03)
        rail.rotation_euler[2] = math.atan2(end[1] - start[1], end[0] - start[0])
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        legs.append(rail)
    
    # Join all components
    bpy.ops.object.select_all(action='DESELECT')
    table.select_set(True)
    for leg in legs:
        leg.select_set(True)
    bpy.context.view_layer.objects.active = table
    bpy.ops.object.join()
    
    # Add material
    material = create_material("table_material", (0.4, 0.2, 0.1, 1))
    table.data.materials.append(material)
    
    return table

def create_chair(chair_data):
    """Create a chair using Blender primitives with proper connections"""
    # Create seat
    dims = chair_data["dimensions"]
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, dims["height"] - dims["thickness"]/2)
    )
    seat = bpy.context.active_object
    seat.scale = (dims["width"], dims["depth"], dims["thickness"])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    # Create chair back
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, dims["depth"]/2, dims["height"] + dims["height"]*0.25)
    )
    back = bpy.context.active_object
    back.scale = (dims["width"], dims["thickness"], dims["height"]*0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    # Create legs with mortise and tenon joints
    legs = []
    leg_positions = [
        (dims["width"]/2 - 0.02, dims["depth"]/2 - 0.02),
        (dims["width"]/2 - 0.02, -dims["depth"]/2 + 0.02),
        (-dims["width"]/2 + 0.02, dims["depth"]/2 - 0.02),
        (-dims["width"]/2 + 0.02, -dims["depth"]/2 + 0.02)
    ]
    
    for pos in leg_positions:
        # Create leg with tenon
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8,
            radius=0.02,  # Leg radius
            depth=dims["height"] - dims["thickness"] + 0.03,  # Extra length for tenon
            location=(pos[0], pos[1], (dims["height"] - dims["thickness"])/2)
        )
        leg = bpy.context.active_object
        
        # Create mortise in seat
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8,
            radius=0.022,  # Slightly larger than leg for fit
            depth=0.03,    # Mortise depth
            location=(pos[0], pos[1], dims["height"] - dims["thickness"])
        )
        mortise = bpy.context.active_object
        
        # Boolean difference to create mortise
        bool_mod = seat.modifiers.new(name="Boolean", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = mortise
        bpy.context.view_layer.objects.active = seat
        bpy.ops.object.modifier_apply(modifier="Boolean")
        
        # Delete mortise object
        bpy.data.objects.remove(mortise)
        
        # Add slight tilt to legs
        leg.rotation_euler = (0.1, 0.1, 0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        legs.append(leg)
    
    # Add support rails
    rails = []
    support_height = dims["height"] - dims["thickness"] - 0.1  # Slightly below seat
    rail_positions = [
        (dims["width"]/2 - 0.02, dims["depth"]/2 - 0.02),
        (dims["width"]/2 - 0.02, -dims["depth"]/2 + 0.02),
        (-dims["width"]/2 + 0.02, dims["depth"]/2 - 0.02),
        (-dims["width"]/2 + 0.02, -dims["depth"]/2 + 0.02)
    ]
    
    for i in range(4):
        start = rail_positions[i]
        end = rail_positions[(i + 1) % 4]
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(
                (start[0] + end[0])/2,
                (start[1] + end[1])/2,
                support_height
            )
        )
        rail = bpy.context.active_object
        length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        rail.scale = (length, 0.02, 0.02)
        rail.rotation_euler[2] = math.atan2(end[1] - start[1], end[0] - start[0])
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        rails.append(rail)
    
    # Join all components
    bpy.ops.object.select_all(action='DESELECT')
    seat.select_set(True)
    back.select_set(True)
    for leg in legs:
        leg.select_set(True)
    for rail in rails:
        rail.select_set(True)
    bpy.context.view_layer.objects.active = seat
    bpy.ops.object.join()
    
    # Add wood material
    material = create_material("chair_material", (0.4, 0.2, 0.1, 1))
    seat.data.materials.append(material)
    
    # Position and rotate chair
    seat.location = chair_data["position"]
    seat.rotation_euler[2] = math.radians(chair_data["rotation"])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
    
    return seat

def create_lamp(lamp_data):
    """Create a lamp using Blender primitives with proper structure"""
    dims = lamp_data["dimensions"]
    lamp_type = lamp_data.get("type", "FloorLamp")
    
    # Create base
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=dims["base_radius"],
        depth=dims["base_height"],
        location=(0, 0, dims["base_height"]/2)
    )
    base = bpy.context.active_object
    
    # Create stand
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8,
        radius=dims["stand_radius"],
        depth=dims["stand_height"],
        location=(0, 0, dims["base_height"] + dims["stand_height"]/2)
    )
    stand = bpy.context.active_object
    
    # Create lampshade
    bpy.ops.mesh.primitive_cone_add(
        vertices=32,
        radius1=dims["shade_bottom_radius"],
        radius2=dims["shade_top_radius"],
        depth=dims["shade_height"],
        location=(0, 0, dims["base_height"] + dims["stand_height"] + dims["shade_height"]/2)
    )
    shade = bpy.context.active_object
    
    # Add curve to stand if needed
    if lamp_type == "FloorLamp":
        bpy.ops.object.modifier_add(type='SIMPLE_DEFORM')
        deform = stand.modifiers["SimpleDeform"]
        deform.deform_method = 'BEND'
        deform.angle = math.radians(30)
        bpy.ops.object.modifier_apply(modifier="SimpleDeform")
    
    # Join components
    bpy.ops.object.select_all(action='DESELECT')
    base.select_set(True)
    stand.select_set(True)
    shade.select_set(True)
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.join()
    
    # Add materials
    base_material = create_material("lamp_base_material", (0.1, 0.1, 0.1, 1))
    shade_material = create_material("lamp_shade_material", (0.9, 0.9, 0.9, 1))
    base.data.materials.append(base_material)
    shade.data.materials.append(shade_material)
    
    return base

def create_window(window_data):
    """Create a window using Blender primitives with proper structure"""
    dims = window_data["dimensions"]
    
    # Create main frame
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, dims["height"]/2)
    )
    frame = bpy.context.active_object
    frame.scale = (dims["width"], dims["frame_thickness"], dims["height"])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    # Create glass panels
    panel_width = (dims["width"] - dims["frame_thickness"] * 2) / dims["panel_h_amount"]
    panel_height = (dims["height"] - dims["frame_thickness"] * 2) / dims["panel_v_amount"]
    
    panels = []
    for i in range(dims["panel_h_amount"]):
        for j in range(dims["panel_v_amount"]):
            x = -dims["width"]/2 + dims["frame_thickness"] + panel_width/2 + i * panel_width
            y = dims["frame_thickness"]/2
            z = -dims["height"]/2 + dims["frame_thickness"] + panel_height/2 + j * panel_height
            
            bpy.ops.mesh.primitive_cube_add(
                size=1,
                location=(x, y, z)
            )
            panel = bpy.context.active_object
            panel.scale = (panel_width - dims["frame_thickness"], dims["glass_thickness"], panel_height - dims["frame_thickness"])
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            panels.append(panel)
    
    # Create mullions
    mullions = []
    for i in range(dims["panel_h_amount"] - 1):
        x = -dims["width"]/2 + dims["frame_thickness"] + panel_width + i * panel_width
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(x, 0, 0)
        )
        mullion = bpy.context.active_object
        mullion.scale = (dims["frame_thickness"], dims["frame_thickness"], dims["height"])
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        mullions.append(mullion)
    
    for j in range(dims["panel_v_amount"] - 1):
        z = -dims["height"]/2 + dims["frame_thickness"] + panel_height + j * panel_height
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(0, 0, z)
        )
        mullion = bpy.context.active_object
        mullion.scale = (dims["width"], dims["frame_thickness"], dims["frame_thickness"])
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        mullions.append(mullion)
    
    # Join all components
    bpy.ops.object.select_all(action='DESELECT')
    frame.select_set(True)
    for panel in panels:
        panel.select_set(True)
    for mullion in mullions:
        mullion.select_set(True)
    bpy.context.view_layer.objects.active = frame
    bpy.ops.object.join()
    
    # Add materials
    frame_material = create_material("window_frame_material", (0.2, 0.2, 0.2, 1))
    glass_material = create_material("window_glass_material", (0.8, 0.8, 0.8, 0.1))
    frame.data.materials.append(frame_material)
    frame.data.materials.append(glass_material)
    
    return frame

def setup_lighting():
    """Setup scene lighting"""
    # Add sun light
    bpy.ops.object.light_add(type='SUN')
    sun = bpy.context.active_object
    sun.rotation_euler = (-0.7, 0.1, 0.22)
    sun.data.energy = 5
    
    # Add ambient light
    bpy.ops.object.light_add(type='AREA')
    ambient = bpy.context.active_object
    ambient.location = (0, 0, 5)
    ambient.data.energy = 2
    ambient.scale = (10, 10, 1)

def setup_camera():
    """Setup camera for rendering"""
    bpy.ops.object.camera_add()
    camera = bpy.context.active_object
    camera.location = (3, -3, 2)
    camera.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = camera

def render_scene(json_path):
    """Main function to render scene from JSON"""
    # Clear existing scene
    clear_scene()
    
    # Load JSON
    with open(json_path, 'r') as f:
        scene_data = json.load(f)
    
    # Create objects
    for obj_data in scene_data["objects"]:
        if obj_data["type"] == "table":
            create_table(obj_data)
        elif obj_data["type"] == "chair":
            create_chair(obj_data)
        elif obj_data["type"] == "lamp":
            create_lamp(obj_data)
        elif obj_data["type"] == "window":
            create_window(obj_data)
    
    # Setup scene
    setup_lighting()
    setup_camera()
    
    # Setup render settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'GPU'
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    
    # Save blend file
    output_dir = Path.home() / "Desktop" / "generated-assets"
    output_dir.mkdir(parents=True, exist_ok=True)
    blend_path = output_dir / "rendered_scene.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    
    # Render image
    render_path = output_dir / "rendered_scene.png"
    bpy.context.scene.render.filepath = str(render_path)
    bpy.ops.render.render(write_still=True)
    
    print(f"Scene saved to: {blend_path}")
    print(f"Render saved to: {render_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_path = sys.argv[-1]
        render_scene(json_path)
    else:
        print("Please provide path to JSON file") 