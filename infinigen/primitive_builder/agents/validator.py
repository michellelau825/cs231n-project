from typing import Dict, List, Tuple
import numpy as np
import openai
from pathlib import Path
import json

class ComponentValidator:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def validate_and_fix(self, components: List[Dict]) -> List[Dict]:
        """Main validation pipeline"""
        print("\n=== Starting Component Validation ===")
        print(f"Validating {len(components)} components...")
        
        # 1. Get connection map from LLM
        connection_map = self._get_connection_map(components)
        print("\nConnection Map:")
        print(json.dumps(connection_map, indent=2))
        
        # 2. FIRST ensure ground contact for legs/base
        components = self._ensure_ground_contact(components)
        print("\nGround contact ensured, proceeding to connections")
        
        # 3. THEN validate and fix connections
        components = self._validate_connections(components, connection_map)
        
        return components

    def _get_connection_map(self, components: List[Dict]) -> Dict[str, List[str]]:
        """Use LLM to determine which components should connect to which"""
        print("\n=== Getting Connection Map ===")
        
        # First try LLM
        system_prompt = """Given these components, output ONLY a connection map showing which components should connect.
        
        Example Input: Table with 4 legs and a top
        Example Output:
        {
            "Table_Top": ["Table_Leg_1", "Table_Leg_2", "Table_Leg_3", "Table_Leg_4"],
            "Table_Leg_1": ["Table_Top"],
            "Table_Leg_2": ["Table_Top"],
            "Table_Leg_3": ["Table_Top"],
            "Table_Leg_4": ["Table_Top"]
        }
        
        DO NOT output component definitions. ONLY output the connection map."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": str([c["name"] for c in components])}  # Only send names
                ],
                temperature=0.2
            )
            
            try:
                result = eval(response.choices[0].message.content)
                print("LLM Connection Map:", json.dumps(result, indent=2))
                return result
            except:
                print("Failed to parse LLM response, using default connections")
                return self._get_default_connections(components)
            
        except Exception as e:
            print(f"Error getting connection map: {e}")
            return self._get_default_connections(components)

    def _get_default_connections(self, components: List[Dict]) -> Dict[str, List[str]]:
        """Create default connections based on component names"""
        print("\nGenerating default connection map...")
        connection_map = {}
        
        # Find the top component
        top_name = next((c["name"] for c in components if "Top" in c["name"]), None)
        
        # Find all leg components
        leg_names = [c["name"] for c in components if "Leg" in c["name"]]
        
        if top_name and leg_names:
            print(f"Found top: {top_name}")
            print(f"Found legs: {leg_names}")
            # Connect top to all legs
            connection_map[top_name] = leg_names
            # Connect each leg to the top
            for leg in leg_names:
                connection_map[leg] = [top_name]
        
        print("Default Connection Map:", json.dumps(connection_map, indent=2))
        return connection_map

    def _validate_connections(self, components: List[Dict], connection_map: Dict[str, List[str]]) -> List[Dict]:
        """Ensure components are properly connected based on connection_map"""
        print("\n=== Validating Component Connections ===")
        
        # Make a copy of components to modify
        updated_components = components.copy()
        
        # FIRST: Check if legs need horizontal adjustment (ONLY FOR CHAIRS, NOT TABLES)
        seat = next((c for c in updated_components if "Seat" in c["name"]), None)
        table_top = next((c for c in updated_components if "Table_Top" in c["name"]), None)
        legs = [c for c in updated_components if "Leg" in c["name"]]
        
        if seat and legs:  # Only adjust leg positions for chairs
            target_points = self._get_connection_point(seat)
            target_bottom = target_points["bottom"]["point"]
            
            for leg in legs:
                leg_idx = next(i for i, c in enumerate(updated_components) if c["name"] == leg["name"])
                leg_points = self._get_connection_point(leg)
                leg_top = leg_points["top"]["point"]
                
                # Check horizontal distance (x,y only)
                horizontal_dist = np.sqrt((leg_top[0] - target_bottom[0])**2 + (leg_top[1] - target_bottom[1])**2)
                if horizontal_dist > 0.1:  # If leg is not under seat
                    print(f"\nLeg {leg['name']} not under seat, horizontal distance: {horizontal_dist}")
                    # Move leg horizontally to seat (chairs only)
                    leg["operations"][0]["transform"]["location"][0] = target_bottom[0]
                    leg["operations"][0]["transform"]["location"][1] = target_bottom[1]
                    updated_components[leg_idx] = leg
                    print(f"Moved leg to seat position: ({target_bottom[0]}, {target_bottom[1]})")
        
        # SECOND: Find highest leg point to snap seat/table to
        highest_leg_z = float('-inf')
        for leg in legs:
            leg_points = self._get_connection_point(leg)
            leg_top = leg_points["top"]["point"]
            highest_leg_z = max(highest_leg_z, leg_top[2])
        
        print(f"\nHighest leg point found: {highest_leg_z}")
        
        # THIRD: Snap seat/table to legs - MOVE DOWN TO LEGS, NOT LEGS UP!
        if seat:
            seat_idx = next(i for i, c in enumerate(updated_components) if c["name"] == seat["name"])
            seat_points = self._get_connection_point(seat)
            seat_bottom = seat_points["bottom"]["point"]
            
            # Calculate how much to move seat
            z_offset = highest_leg_z - seat_bottom[2]
            print(f"Moving seat to match leg height, offset: {z_offset}")
            
            # Update seat location
            seat["operations"][0]["transform"]["location"][2] += z_offset
            updated_components[seat_idx] = seat
            print(f"Snapped seat to legs at height {highest_leg_z}")
        elif table_top:  # Handle table top ONCE, only Z-axis
            table_idx = next(i for i, c in enumerate(updated_components) if c["name"] == table_top["name"])
            table_points = self._get_connection_point(table_top)
            table_bottom = table_points["bottom"]["point"]
            
            # Calculate how much to move table (Z only)
            z_offset = highest_leg_z - table_bottom[2]
            print(f"Moving table to match leg height, offset: {z_offset}")
            
            # Update ONLY table Z location
            table_top["operations"][0]["transform"]["location"][2] += z_offset
            updated_components[table_idx] = table_top
            print(f"Snapped table to legs at height {highest_leg_z}")
        
        # FOURTH: Handle any remaining connections (like backrest)
        for comp_name, should_connect_to in connection_map.items():
            if "Leg" not in comp_name and "Seat" not in comp_name and "Table_Top" not in comp_name:  # Skip legs and seat/table as we handled them
                comp_idx = next((i for i, c in enumerate(updated_components) if c["name"] == comp_name), None)
                if comp_idx is None:
                    continue
                    
                comp = updated_components[comp_idx]
                print(f"\nChecking connections for {comp_name}:")
                comp_points = self._get_connection_point(comp)
                
                for target_name in should_connect_to:
                    target = next((c for c in updated_components if c["name"] == target_name), None)
                    if not target:
                        continue
                        
                    target_points = self._get_connection_point(target)
                    
                    # Extract actual points from the dictionaries
                    if "Backrest" in comp_name:
                        comp_point = comp_points["bottom"]["point"]
                        target_point = target_points["top"]["point"]
                    else:
                        comp_point = max(comp_points.values(), key=lambda x: x['priority'])['point']
                        target_point = max(target_points.values(), key=lambda x: x['priority'])['point']
                    
                    print(f"  Checking connection to {target_name}:")
                    print(f"    Component point: {comp_point}")
                    print(f"    Target point: {target_point}")
                    
                    if not self._are_points_connected(comp_point, target_point):
                        print(f"    Points not connected! Distance: {np.linalg.norm(comp_point - target_point):.3f}")
                        updated_comp = self._snap_to_point(comp, comp_point, target_point)
                        updated_components[comp_idx] = updated_comp
        
        return updated_components

    def _ensure_ground_contact(self, components: List[Dict]) -> List[Dict]:
        """Ensure base components touch the ground"""
        print("\n=== Ensuring Ground Contact ===")
        ground_level = 0  # Assuming ground is at z=0
        
        # First find the lowest point of the base component (Bed_Frame, Table_Base, etc)
        base_components = [c for c in components if any(base in c["name"].lower() for base in ["frame", "base", "leg"])]
        if base_components:
            base_lowest_points = [self._get_lowest_point(base) for base in base_components]
            print(f"Base component lowest points: {base_lowest_points}")
            ground_adjustment = min(base_lowest_points) - ground_level
            print(f"Ground adjustment needed: {ground_adjustment}")
            
            # First adjust base components to ground
            for comp in base_components:
                try:
                    if comp["operations"][0]["operation"] == "draw.bezier_curve":
                        # For bezier curves, adjust all anchor points
                        anchors = comp["operations"][0]["params"]["anchors"]
                        adjusted_anchors = [[x, y, z - ground_adjustment] for x, y, z in anchors]
                        comp["operations"][0]["params"]["anchors"] = adjusted_anchors
                    else:
                        # For regular components, adjust transform
                        comp["operations"][0]["transform"]["location"][2] -= ground_adjustment
                    print(f"Adjusted {comp['name']} to ground level")
                except Exception as e:
                    print(f"Warning: Could not adjust {comp['name']}: {e}")
            
            # Then adjust all other components to maintain relative positions
            for comp in components:
                if comp not in base_components:
                    try:
                        comp["operations"][0]["transform"]["location"][2] -= ground_adjustment
                        print(f"Adjusted {comp['name']} by same amount to maintain relative position")
                    except Exception as e:
                        print(f"Warning: Could not adjust {comp['name']}: {e}")

        return components

    def _get_connection_point(self, component: Dict) -> Dict[str, Dict[str, np.ndarray]]:
        """Get the point where this component should connect to others"""
        try:
            operation = component["operations"][0]
            transform = operation.get("transform", {})
            location = transform.get("location", [0, 0, 0])
            scale = transform.get("scale", [1, 1, 1])
            
            print(f"\nCalculating connection point for {component['name']}:")
            print(f"  Operation: {operation['operation']}")
            print(f"  Transform: {transform}")
            
            if operation["operation"] == "mesh.build_sphere_mesh":
                radius = operation["params"].get("radius", 0.5)
                scaled_radius = radius * scale[2]  # Use z-scale for vertical radius
                top_point = np.array([
                    location[0],
                    location[1],
                    location[2] + scaled_radius
                ])
                bottom_point = np.array([
                    location[0],
                    location[1],
                    location[2] - scaled_radius
                ])
                print(f"  Sphere - Top: {top_point}, Bottom: {bottom_point}")
                return {
                    "top": {"point": top_point, "priority": 1},
                    "bottom": {"point": bottom_point, "priority": 1},
                    "center": {"point": np.array(location), "priority": 0}
                }
            
            elif operation["operation"] == "mesh.build_cylinder_mesh":
                height = operation["params"].get("height", 1.0)
                scaled_height = height * scale[2]
                top_point = np.array([
                    location[0],
                    location[1],
                    location[2] + scaled_height/2
                ])
                bottom_point = np.array([
                    location[0],
                    location[1],
                    location[2] - scaled_height/2
                ])
                print(f"  Cylinder - Top: {top_point}, Bottom: {bottom_point}")
                return {
                    "top": {"point": top_point, "priority": 1},
                    "bottom": {"point": bottom_point, "priority": 1},
                    "center": {"point": np.array(location), "priority": 0}
                }
            
            elif operation["operation"] == "mesh.build_box_mesh":
                height = operation["params"].get("height", 1.0)
                scaled_height = height * scale[2]
                top_point = np.array([
                    location[0],
                    location[1],
                    location[2] + scaled_height/2
                ])
                bottom_point = np.array([
                    location[0],
                    location[1],
                    location[2] - scaled_height/2
                ])
                print(f"  Box - Top: {top_point}, Bottom: {bottom_point}")
                return {
                    "top": {"point": top_point, "priority": 1},
                    "bottom": {"point": bottom_point, "priority": 1},
                    "center": {"point": np.array(location), "priority": 0}
                }
            
            print(f"  Default center point: {location}")
            return {
                "center": {"point": np.array(location), "priority": 0}
            }
        
        except Exception as e:
            print(f"Error getting connection point for {component['name']}: {e}")
            return {
                "center": {"point": np.array([0, 0, 0]), "priority": 0}
            }

    def _are_points_connected(self, point1: np.ndarray, point2: np.ndarray, threshold: float = 0.01) -> bool:
        """Check if two points are close enough to be considered connected"""
        if point1 is None or point2 is None:
            return False
        return np.linalg.norm(point1 - point2) < threshold

    def _snap_to_point(self, component: Dict, from_point: np.ndarray, to_point: np.ndarray) -> Dict:
        """Move component so that from_point aligns with to_point"""
        print(f"\nSnapping {component['name']}:")
        print(f"  From point: {from_point}")
        print(f"  To point: {to_point}")
        
        try:
            # For legs, only adjust Z coordinate
            if "Leg" in component["name"]:
                current_location = component["operations"][0]["transform"]["location"]
                print(f"  Current location: {current_location}")
                
                # Only calculate Z offset
                z_offset = to_point[2] - from_point[2]
                print(f"  Z offset to apply: {z_offset}")
                
                if component["operations"][0]["operation"] == "draw.bezier_curve":
                    # For bezier curves, adjust all anchor points
                    anchors = component["operations"][0]["params"]["anchors"]
                    print(f"  Original anchors: {anchors}")
                    adjusted_anchors = [[x, y, z + z_offset] for x, y, z in anchors]
                    component["operations"][0]["params"]["anchors"] = adjusted_anchors
                    print(f"  Adjusted anchors: {adjusted_anchors}")
                else:
                    # For other legs, adjust transform location
                    new_location = [
                        current_location[0],
                        current_location[1],
                        current_location[2] + z_offset
                    ]
                    component["operations"][0]["transform"]["location"] = new_location
                
            # For seat/top, keep centered and only adjust Z if needed
            elif "Seat" in component["name"] or "Top" in component["name"]:
                current_location = component["operations"][0]["transform"]["location"]
                print(f"  Current location: {current_location}")
                
                # Only adjust Z if needed
                z_offset = to_point[2] - from_point[2]
                print(f"  Z offset to apply: {z_offset}")
                
                new_location = [
                    current_location[0],
                    current_location[1],
                    current_location[2] + z_offset
                ]
                
                component["operations"][0]["transform"]["location"] = new_location
                print(f"  New location: {new_location}")
            
            return component
            
        except Exception as e:
            print(f"Error in snap_to_point for {component['name']}: {e}")
            print(f"Component structure: {json.dumps(component, indent=2)}")
            return component

    def _get_lowest_point(self, component: Dict) -> float:
        """Get the lowest z-coordinate of a component based on its operation and transform"""
        print(f"\nGetting lowest point for {component['name']}:")
        operation = component["operations"][0]["operation"]
        params = component["operations"][0]["params"]
        transform = component["operations"][0].get("transform", {})
        location = transform.get("location", [0, 0, 0])
        print(f"  Operation: {operation}")
        print(f"  Location: {location}")

        if operation == "draw.bezier_curve":
            # For curves, check all anchor points
            anchors = params["anchors"]
            lowest_anchor = min(point[2] for point in anchors)
            print(f"  Bezier curve - Checking all anchors. Lowest z: {lowest_anchor}")
            return lowest_anchor
        
        elif operation == "mesh.build_cylinder_mesh":
            height = params["height"]
            lowest = location[2] - height/2
            print(f"  Cylinder - Height: {height}, Lowest z: {lowest}")
            return lowest
        
        elif operation == "mesh.build_box_mesh":
            height = params["height"]
            lowest = location[2] - height/2
            print(f"  Box - Height: {height}, Lowest z: {lowest}")
            return lowest
        
        elif operation == "mesh.build_sphere_mesh":
            radius = params["radius"]
            lowest = location[2] - radius
            print(f"  Sphere - Radius: {radius}, Lowest z: {lowest}")
            return lowest
        
        else:
            print(f"Warning: Unknown operation type {operation}, using location z")
            return location[2]

