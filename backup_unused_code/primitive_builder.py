import bpy
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from infinigen.assets.utils.draw import (
    bezier_curve, align_bezier, spin, leaf, shape_by_angles,
    shape_by_xs, curve2mesh, remesh_fill, cut_plane
)
from infinigen.assets.utils.mesh import build_prism_mesh, build_convex_mesh
from infinigen.assets.utils.decorate import displace_vertices, solidify
from infinigen.assets.utils.object import (
    obj2trimesh, center, join_objects, new_cube, new_cylinder,
    new_plane, new_empty
)
from infinigen.core.util import blender as butil
from infinigen.primitive_builder.llm_client import LLMClient
from infinigen.core import surface
from pathlib import Path
from .primitive_agent import PrimitiveAgent

@dataclass
class PrimitiveSpec:
    """Specification for a primitive geometry operation"""
    operation: str  # Name of the primitive function to call
    params: Dict[str, Any]  # Parameters for the operation
    transform: Optional[Dict[str, Any]] = None  # Optional transformation to apply
    material: Optional[str] = None  # Optional material to apply

class PrimitiveBuilder:
    """Low-level builder for creating objects using primitive geometry functions"""
    
    def __init__(self):
        self.agent = PrimitiveAgent()
    
    def build(self, prompt: str) -> bpy.types.Object:
        """Build a 3D object from a prompt"""
        # Get specifications from agent
        specs = self.agent.generate_specs(prompt)
        
        # Create components
        components = []
        for spec in specs:
            op = spec["operation"]
            params = spec["params"]
            transform = spec.get("transform", {})
            
            # Create the base object
            if op == "build_prism_mesh":
                from infinigen.assets.utils.draw import build_prism_mesh
                mesh = build_prism_mesh(**params)
                obj = bpy.data.objects.new(f"component_{len(components)}", mesh)
                bpy.context.scene.collection.objects.link(obj)
                
            elif op == "bezier_curve":
                from infinigen.assets.utils.draw import bezier_curve
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
    
    def save(self, obj: bpy.types.Object, output_path: Path):
        """Save the object to a .blend file"""
        output_path.parent.mkdir(exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

class LLMInterpreter:
    """Interprets natural language descriptions into primitive specifications"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
    def interpret_description(self, description: str) -> List[PrimitiveSpec]:
        """Convert natural language description to primitive specifications"""
        # Use LLM to break down the description into primitive operations
        response = self.llm_client.analyze_description(description)
        
        # Convert LLM response to primitive specifications
        specs = []
        for op in response['operations']:
            spec = PrimitiveSpec(
                operation=op['type'],
                params=op['parameters'],
                transform=op.get('transform'),
                material=op.get('material')
            )
            specs.append(spec)
        
        return specs

class ProceduralSceneBuilder:
    """High-level builder for creating procedural scenes"""
    
    def __init__(self, llm_client):
        self.primitive_builder = PrimitiveBuilder()
        self.llm_interpreter = LLMInterpreter(llm_client)
        self.llm_client = llm_client
        self.floor_height = 0
        self.wall_height = 3.0
        self.room_size = 5.0
        
    def build_from_description(self, description: str) -> bpy.types.Object:
        """Build a scene from a natural language description"""
        # Clear existing scene
        butil.clear_scene()
        
        # Create floor
        self._create_floor()
        
        # Create walls
        self._create_walls()
        
        # Parse description and create objects
        objects = self._create_objects(description)
        
        # Position objects realistically
        self._position_objects(objects)
        
        return objects

    def _create_floor(self):
        """Create a floor plane"""
        bpy.ops.mesh.primitive_plane_add(size=self.room_size)
        floor = bpy.context.active_object
        floor.name = "Floor"
        floor.location = (0, 0, self.floor_height)
        
        # Add floor material
        material = bpy.data.materials.new(name="Floor_Material")
        material.use_nodes = True
        floor.data.materials.append(material)

    def _create_walls(self):
        """Create room walls"""
        wall_height = self.wall_height
        room_size = self.room_size
        
        # Create four walls
        for i in range(4):
            angle = i * np.pi/2
            x = np.cos(angle) * room_size/2
            y = np.sin(angle) * room_size/2
            
            bpy.ops.mesh.primitive_plane_add(size=room_size)
            wall = bpy.context.active_object
            wall.name = f"Wall_{i}"
            
            # Position and rotate wall
            wall.location = (x, y, wall_height/2)
            wall.rotation_euler = (0, 0, angle)
            
            # Add wall material
            material = bpy.data.materials.new(name=f"Wall_Material_{i}")
            material.use_nodes = True
            wall.data.materials.append(material)

    def _create_objects(self, description):
        """Create objects based on description"""
        # Get object parameters from LLM
        params = self.llm_client.get_object_parameters(description)
        
        objects = []
        for obj_type, obj_params in params.items():
            if obj_type == "table":
                obj = self._create_table(obj_params)
            elif obj_type == "chair":
                obj = self._create_chair(obj_params)
            elif obj_type == "lamp":
                obj = self._create_lamp(obj_params)
            else:
                continue
            objects.append(obj)
            
        return objects

    def _create_table(self, params):
        """Create a table with proper orientation"""
        # Create table top
        bpy.ops.mesh.primitive_cube_add()
        table_top = bpy.context.active_object
        table_top.name = "Table_Top"
        table_top.scale = (params.get('width', 1.0), params.get('depth', 0.8), params.get('thickness', 0.05))
        table_top.location = (0, 0, params.get('height', 0.75))
        
        # Create legs
        leg_positions = [
            (-0.4, -0.3, 0), (0.4, -0.3, 0),
            (-0.4, 0.3, 0), (0.4, 0.3, 0)
        ]
        
        legs = []
        for i, pos in enumerate(leg_positions):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=params.get('height', 0.75))
            leg = bpy.context.active_object
            leg.name = f"Table_Leg_{i}"
            leg.location = (pos[0], pos[1], params.get('height', 0.75)/2)
            legs.append(leg)
        
        # Join all parts
        table = butil.join_objects([table_top] + legs)
        table.name = "Table"
        
        return table

    def _create_chair(self, params):
        """Create a chair with proper orientation"""
        # Create seat
        bpy.ops.mesh.primitive_cube_add()
        seat = bpy.context.active_object
        seat.name = "Chair_Seat"
        seat.scale = (params.get('width', 0.5), params.get('depth', 0.5), params.get('thickness', 0.05))
        seat.location = (0, 0, params.get('height', 0.45))
        
        # Create backrest
        bpy.ops.mesh.primitive_cube_add()
        backrest = bpy.context.active_object
        backrest.name = "Chair_Backrest"
        backrest.scale = (params.get('width', 0.5), params.get('thickness', 0.05), params.get('back_height', 0.5))
        backrest.location = (0, -params.get('depth', 0.5)/2, params.get('height', 0.45) + params.get('back_height', 0.5)/2)
        
        # Create legs
        leg_positions = [
            (-0.2, -0.2, 0), (0.2, -0.2, 0),
            (-0.2, 0.2, 0), (0.2, 0.2, 0)
        ]
        
        legs = []
        for i, pos in enumerate(leg_positions):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=params.get('height', 0.45))
            leg = bpy.context.active_object
            leg.name = f"Chair_Leg_{i}"
            leg.location = (pos[0], pos[1], params.get('height', 0.45)/2)
            legs.append(leg)
        
        # Join all parts
        chair = butil.join_objects([seat, backrest] + legs)
        chair.name = "Chair"
        
        return chair

    def _create_lamp(self, params):
        """Create a lamp with proper orientation"""
        # Create base
        bpy.ops.mesh.primitive_cylinder_add(radius=params.get('base_radius', 0.2), depth=params.get('base_height', 0.05))
        base = bpy.context.active_object
        base.name = "Lamp_Base"
        base.location = (0, 0, params.get('base_height', 0.05)/2)
        
        # Create pole
        bpy.ops.mesh.primitive_cylinder_add(radius=params.get('pole_radius', 0.02), depth=params.get('height', 1.2))
        pole = bpy.context.active_object
        pole.name = "Lamp_Pole"
        pole.location = (0, 0, params.get('height', 1.2)/2 + params.get('base_height', 0.05))
        
        # Create shade
        bpy.ops.mesh.primitive_cone_add(radius1=params.get('shade_radius', 0.3), radius2=0, depth=params.get('shade_height', 0.4))
        shade = bpy.context.active_object
        shade.name = "Lamp_Shade"
        shade.location = (0, 0, params.get('height', 1.2) + params.get('shade_height', 0.4)/2)
        
        # Join all parts
        lamp = butil.join_objects([base, pole, shade])
        lamp.name = "Lamp"
        
        return lamp

    def _position_objects(self, objects):
        """Position objects realistically in the room"""
        # Group objects by type
        tables = [obj for obj in objects if "Table" in obj.name]
        chairs = [obj for obj in objects if "Chair" in obj.name]
        lamps = [obj for obj in objects if "Lamp" in obj.name]
        
        # Position tables
        for i, table in enumerate(tables):
            angle = i * np.pi/2
            radius = self.room_size * 0.3
            x = np.cos(angle) * radius
            y = np.sin(angle) * radius
            table.location = (x, y, 0)
            table.rotation_euler = (0, 0, angle)
            
            # Position chairs around table
            table_chairs = chairs[i*4:(i+1)*4]
            for j, chair in enumerate(table_chairs):
                chair_angle = angle + j * np.pi/2
                chair_radius = radius + 0.6
                chair_x = np.cos(chair_angle) * chair_radius
                chair_y = np.sin(chair_angle) * chair_radius
                chair.location = (chair_x, chair_y, 0)
                chair.rotation_euler = (0, 0, chair_angle + np.pi)
        
        # Position lamps in corners
        for i, lamp in enumerate(lamps):
            angle = (i * np.pi/2) + np.pi/4
            radius = self.room_size * 0.4
            x = np.cos(angle) * radius
            y = np.sin(angle) * radius
            lamp.location = (x, y, 0)

# Example usage:
"""
# Initialize the builder with an LLM client
llm_client = YourLLMClient()  # Replace with actual LLM client
builder = ProceduralSceneBuilder(llm_client)

# Build an object from description
obj = builder.build_from_description(
    "Create a modern wooden chair with curved backrest and four straight legs"
)

# The LLM would break this down into primitive operations like:
# 1. Create base seat using bezier_curve
# 2. Create backrest using align_bezier
# 3. Create legs using build_prism_mesh
# 4. Apply transformations to position everything
# 5. Apply materials
""" 