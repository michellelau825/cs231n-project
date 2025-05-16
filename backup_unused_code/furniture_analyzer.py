import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class ComponentType(Enum):
    SEAT = "seat"
    BACK = "back"
    LEG = "leg"
    ARM = "arm"
    SUPPORT = "support"
    TABLE_TOP = "table_top"
    DRAWER = "drawer"
    SHELF = "shelf"
    DOOR = "door"

class ConnectionType(Enum):
    MORTISE_TENON = "mortise_tenon"
    DOWEL = "dowel"
    SCREW = "screw"
    GLUE = "glue"
    WELD = "weld"
    SLIDE = "slide"
    HINGE = "hinge"

@dataclass
class Component:
    name: str
    type: ComponentType
    dimensions: Dict[str, float]  # width, depth, height in meters
    position: Dict[str, float]    # x, y, z in meters
    rotation: Dict[str, float]    # x, y, z in degrees
    material_thickness: float     # in meters
    connections: List[str]        # names of connected components
    support_points: List[List[float]]  # [[x,y,z], ...]
    features: List[str]

class FurnitureAnalyzer:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
    def analyze_furniture_structure(self, furniture_type: str, style: str = "modern") -> Dict:
        """Get detailed structural analysis of furniture from LLM"""
        prompt = f"""
        Analyze the physical structure of a {style} {furniture_type}. Provide detailed information about its components and their relationships.
        
        For each component, specify:
        1. Exact dimensions in meters
        2. Precise position relative to the furniture's base
        3. Rotation angles in degrees
        4. Material thickness in meters
        5. How it connects to other components
        6. Support points and load distribution
        
        For a chair, for example:
        - The seat should be at the base (z=0)
        - Legs should connect to the bottom of the seat
        - Back should be above the seat
        - Arms (if present) should be at seat height
        - Support rails should connect the legs
        
        For a table:
        - Table top should be at the specified height
        - Legs should connect to the bottom of the table top
        - Support structure should be between legs
        
        Format the response as a JSON with the following structure:
        {{
            "components": [
                {{
                    "name": "component_name",
                    "type": "seat|back|leg|arm|support|table_top|drawer|shelf|door",
                    "dimensions": {{"width": float, "depth": float, "height": float}},
                    "position": {{"x": float, "y": float, "z": float}},
                    "rotation": {{"x": float, "y": float, "z": float}},
                    "material_thickness": float,
                    "connections": ["component_name1", "component_name2"],
                    "support_points": [[x, y, z], ...],
                    "features": ["feature1", "feature2"]
                }}
            ],
            "structural_requirements": [
                "requirement1",
                "requirement2"
            ],
            "style_elements": [
                "element1",
                "element2"
            ],
            "assembly_order": [
                "component1",
                "component2",
                ...
            ]
        }}
        """
        
        response = self.llm_client.get_structured_response(prompt)
        return json.loads(response)
    
    def get_component_connections(self, component1: str, component2: str, style: str) -> List[Dict]:
        """Get detailed information about how two components connect"""
        prompt = f"""
        Describe how a {style} {component1} connects to a {component2}. Be very specific about:
        1. Connection type (mortise_tenon, dowel, screw, glue, weld, slide, hinge)
        2. Exact connection points and their coordinates relative to each component
        3. Required hardware or joinery with specific dimensions
        4. Structural considerations and load distribution
        
        For example, for a chair leg connecting to the seat:
        - Mortise hole in seat: 2cm diameter, 3cm deep
        - Tenon on leg: 1.8cm diameter, 3.5cm long
        - Glue application points
        - Support brackets if needed
        
        Format as JSON:
        {{
            "connection_type": "mortise_tenon|dowel|screw|glue|weld|slide|hinge",
            "connection_points": [
                {{
                    "component1_point": [x, y, z],
                    "component2_point": [x, y, z],
                    "hardware": {{
                        "type": "string",
                        "dimensions": {{"width": float, "depth": float, "height": float}},
                        "quantity": int
                    }},
                    "joinery": {{
                        "type": "string",
                        "dimensions": {{"width": float, "depth": float, "height": float}},
                        "tolerance": float
                    }}
                }}
            ],
            "structural_notes": ["note1", "note2"],
            "load_distribution": {{
                "point1": "description",
                "point2": "description"
            }}
        }}
        """
        
        response = self.llm_client.get_structured_response(prompt)
        return json.loads(response)
    
    def get_support_structure(self, furniture_type: str, style: str) -> Dict:
        """Get information about the support structure of furniture"""
        prompt = f"""
        Analyze the support structure of a {style} {furniture_type}. Be very specific about:
        1. Primary support points with exact coordinates
        2. Load distribution and weight capacity
        3. Required reinforcement with exact dimensions
        4. Material thickness requirements
        5. Stress points and how they're handled
        
        For example, for a chair:
        - Seat support: 4 points at leg connections
        - Back support: 2 points at back-to-seat connection
        - Arm support: 2 points at arm-to-back connection
        - Leg reinforcement: cross rails at 1/3 and 2/3 height
        
        Format as JSON:
        {{
            "support_points": [
                {{
                    "location": [x, y, z],
                    "load_capacity": float,
                    "type": "primary|secondary|reinforcement"
                }}
            ],
            "load_distribution": {{
                "point1": {{
                    "description": "string",
                    "weight_capacity": float,
                    "stress_points": [[x, y, z], ...]
                }}
            }},
            "reinforcement": [
                {{
                    "location": [x, y, z],
                    "type": "string",
                    "dimensions": {{"width": float, "depth": float, "height": float}},
                    "material": "string",
                    "connection_points": [[x, y, z], ...]
                }}
            ],
            "stress_points": [
                {{
                    "location": [x, y, z],
                    "type": "tension|compression|shear",
                    "reinforcement": "string"
                }}
            ]
        }}
        """
        
        response = self.llm_client.get_structured_response(prompt)
        return json.loads(response) 