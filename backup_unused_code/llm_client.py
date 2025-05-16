import os
from typing import Dict, Any, List, Tuple
import bpy
from dataclasses import dataclass
import json
import openai

@dataclass
class PrimitiveSpec:
    operation: str
    params: Dict[str, Any]
    transform: Dict[str, Any] = None

class LLMClient:
    """Client for generating scene parameters"""
    
    def __init__(self):
        # Initialize OpenAI client
        self.client = openai.OpenAI()
        self.model = "gpt-4"
        
        # Core primitive operations
        self.primitive_operations = {
            'build_prism_mesh': 'Creates a prismatic mesh with n sides',
            'bezier_curve': 'Creates a curved shape using bezier points',
            'align_bezier': 'Creates an aligned bezier curve',
            'spin': 'Creates a surface by spinning a curve',
            'leaf': 'Creates a leaf-like shape'
        }

    def get_scene_parameters(self, description: str) -> Dict[str, Any]:
        """Get complete scene parameters from description"""
        # Return hardcoded parameters for now
        return {
            'scene_context': {
                'room_type': 'dining_room',
                'time_of_day': 'day',
                'style': 'modern',
                'objects': ['table', 'chairs'],
                'lighting': 'natural'
            },
            'objects': [
                {
                    'type': 'table',
                    'width': 180,
                    'depth': 90,
                    'height': 75,
                    'thickness': 5,
                    'material': 'wood',
                    'style': 'modern'
                },
                {
                    'type': 'chair',
                    'width': 45,
                    'depth': 45,
                    'height': 90,
                    'thickness': 5,
                    'back_height': 45,
                    'material': 'wood',
                    'style': 'modern'
                }
            ],
            'lighting': {
                'type': 'natural',
                'intensity': 5.0,
                'color_temperature': 5500,
                'direction': [45, 0, 45],
                'number_of_sources': 1
            },
            'camera': {
                'position': [3, -3, 2],
                'angle': [60, 0, 45],
                'field_of_view': 60,
                'focal_length': 35
            }
        }

    def get_default_response(self, description: str) -> Dict[str, Any]:
        """Get a default response for common objects"""
        if "chair" in description.lower():
            return {
                "operations": [
                    {
                        "type": "cube",
                        "parameters": {
                            "location": [0, 0, 0.5],
                            "scale": [0.4, 0.4, 0.05]
                        },
                        "material": "wood"
                    },
                    {
                        "type": "cube",
                        "parameters": {
                            "location": [0, 0.2, 0.8],
                            "scale": [0.4, 0.05, 0.6]
                        },
                        "material": "wood"
                    },
                    {
                        "type": "cylinder",
                        "parameters": {
                            "location": [0.15, 0.15, 0.25],
                            "depth": 0.5,
                            "radius": 0.02
                        },
                        "material": "wood"
                    }
                ]
            }
        return {
            "operations": [
                {
                    "type": "cube",
                    "parameters": {
                        "location": [0, 0, 0],
                        "scale": [1, 1, 1]
                    }
                }
            ]
        }

    def analyze_description(self, description: str) -> Dict[str, Any]:
        """Analyze a natural language description and convert it to primitive operations"""
        
        # Create the messages for the API call
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Analyze this object description and convert it to primitive operations. Respond with ONLY the JSON object, no other text: {description}"}
        ]
        
        try:
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            
            # Get the response content
            content = response.choices[0].message.content.strip()
            
            # Try to parse the JSON response
            try:
                result = json.loads(content)
                if "operations" not in result:
                    raise ValueError("Response missing 'operations' key")
                return result
            except json.JSONDecodeError:
                print(f"Failed to parse LLM response as JSON. Using default response. Raw response: {content}")
                return self.get_default_response(description)
                
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return self.get_default_response(description)

    def analyze_prompt(self, prompt: str) -> list:
        """Convert prompt to primitive specifications"""
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
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            specs = eval(response.choices[0].message.content)
            return specs
            
        except Exception as e:
            print(f"Error generating specifications: {e}")
            return [{
                "operation": "build_prism_mesh",
                "params": {"n": 4, "r_min": 0.5, "r_max": 0.5, "height": 0.1},
                "transform": {"location": [0, 0, 0]}
            }]

    def create_object(self, prompt: str) -> bpy.types.Object:
        """Create a Blender object from the prompt"""
        # Clear existing scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        # Get primitive specifications
        specs = self.analyze_prompt(prompt)
        
        # Create objects from specifications
        components = []
        for spec in specs:
            if spec["operation"] == "build_prism_mesh":
                from infinigen.assets.utils.mesh import build_prism_mesh
                mesh = build_prism_mesh(**spec["params"])
                obj = bpy.data.objects.new(f"component_{len(components)}", mesh)
                bpy.context.scene.collection.objects.link(obj)
                if spec["transform"]:
                    obj.location = spec["transform"].get("location", (0,0,0))
                components.append(obj)
                
            elif spec["operation"] == "bezier_curve":
                from infinigen.assets.utils.draw import bezier_curve
                curve = bezier_curve(**spec["params"])
                components.append(curve)
                
            elif spec["operation"] == "align_bezier":
                from infinigen.assets.utils.draw import align_bezier
                curve = align_bezier(**spec["params"])
                components.append(curve)
        
        # Join all components
        if components:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in components:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = components[0]
            bpy.ops.object.join()
            return components[0]
        
        return None

# Example usage:
"""
client = LLMClient()

# Example description
description = "Create a modern wooden chair with curved backrest and four straight legs"

# Get primitive operations
operations = client.analyze_description(description)

# Example response might look like:
{
    "operations": [
        {
            "type": "bezier_curve",
            "parameters": {
                "anchors": [[0,0,0], [0.4,0,0.05], [0.4,0.4,0.05], [0,0.4,0]],
                "resolution": 32
            },
            "material": "wood"
        },
        {
            "type": "align_bezier",
            "parameters": {
                "anchors": [[0,0.4,0], [0,0.4,0.6]],
                "axes": [[0,1,0]],
                "scale": [1.2]
            },
            "transform": {
                "location": [0.2, 0.2, 0]
            },
            "material": "wood"
        },
        {
            "type": "build_prism_mesh",
            "parameters": {
                "n": 4,
                "r_min": 0.02,
                "r_max": 0.02,
                "height": 0.4
            },
            "transform": {
                "location": [0.1, 0.1, 0]
            },
            "material": "wood"
        }
        # ... more operations for other legs
    ]
}
""" 