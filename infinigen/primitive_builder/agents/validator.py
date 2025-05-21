import openai
from typing import Dict, List, Tuple, Set
import json
import math
import numpy as np

class ComponentValidator:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def validate_and_fix(self, components: List[Dict]) -> List[Dict]:
        print("\n=== Starting Component Validation ===")
        print("Checking component connections and alignments...")
        
        # First pass: Build connectivity graph and identify floating components
        connectivity_graph = self._build_connectivity_graph(components)
        
        # Second pass: Add missing connections and align components
        fixed_components = self._fix_connections(components, connectivity_graph)
        
        # Third pass: Validate all connections are physically possible
        validated_components = self._validate_physical_connections(fixed_components)
        
        # Final pass: LLM verification of all positions and rotations
        final_components = self._final_position_check(validated_components)
        
        return final_components
    
    def _build_connectivity_graph(self, components: List[Dict]) -> Dict[str, Set[str]]:
        """Build a graph of component connections"""
        graph = {comp['name']: set() for comp in components}
        
        for comp1 in components:
            for comp2 in components:
                if comp1['name'] != comp2['name']:
                    if self._are_components_connected(comp1, comp2):
                        graph[comp1['name']].add(comp2['name'])
                        graph[comp2['name']].add(comp1['name'])
        
        print("\nInitial Connectivity Graph:")
        for comp, connections in graph.items():
            print(f"{comp}: {connections}")
        
        return graph
    
    def _are_components_connected(self, comp1: Dict, comp2: Dict) -> bool:
        """Check if two components are physically connected"""
        for op1 in comp1.get('operations', []):
            transform1 = op1.get('transform', {})
            params1 = op1.get('params', {})
            
            for op2 in comp2.get('operations', []):
                transform2 = op2.get('transform', {})
                params2 = op2.get('params', {})
                
                if not (transform1 and transform2 and params1 and params2):
                    continue
                
                # Get component boundaries
                bounds1 = self._get_component_bounds(transform1, params1)
                bounds2 = self._get_component_bounds(transform2, params2)
                
                # Check if components touch
                if self._bounds_intersect(bounds1, bounds2):
                    return True
        
        return False
    
    def _get_component_bounds(self, transform: Dict, params: Dict) -> Dict:
        """Calculate component boundaries based on transform and params"""
        loc = transform.get('location', [0, 0, 0])
        width = params.get('width', 0)
        depth = params.get('depth', 0)
        height = params.get('height', 0)
        radius = params.get('radius', 0)
        
        # Handle different primitive types
        if radius:  # Cylindrical components
            return {
                'min': [loc[0] - radius, loc[1] - radius, loc[2] - height/2],
                'max': [loc[0] + radius, loc[1] + radius, loc[2] + height/2]
            }
        else:  # Box-like components
            return {
                'min': [loc[0] - width/2, loc[1] - depth/2, loc[2] - height/2],
                'max': [loc[0] + width/2, loc[1] + depth/2, loc[2] + height/2]
            }
    
    def _bounds_intersect(self, bounds1: Dict, bounds2: Dict, tolerance: float = 0.001) -> bool:
        """Check if two bounds intersect or touch within tolerance"""
        for i in range(3):
            if (bounds1['max'][i] + tolerance < bounds2['min'][i] or 
                bounds2['max'][i] + tolerance < bounds1['min'][i]):
                return False
        return True
    
    def _fix_connections(self, components: List[Dict], graph: Dict[str, Set[str]]) -> List[Dict]:
        """Add connecting components where needed"""
        fixed_components = components.copy()
        added_connectors = []
        
        # Find disconnected components
        for comp1 in components:
            for comp2 in components:
                if (comp1['name'] != comp2['name'] and 
                    comp2['name'] not in graph[comp1['name']]):
                    
                    # Check if we need a connector
                    if self._needs_connector(comp1, comp2):
                        connector = self._create_connector(comp1, comp2)
                        if connector:
                            added_connectors.append(connector)
                            print(f"\nAdded connector between {comp1['name']} and {comp2['name']}")
        
        fixed_components.extend(added_connectors)
        return fixed_components
    
    def _needs_connector(self, comp1: Dict, comp2: Dict) -> bool:
        """Determine if two components need a connecting piece"""
        # Example: Chair back needs support to connect to seat
        if ('back' in comp1['name'].lower() and 'seat' in comp2['name'].lower()):
            return True
        # Example: Armrest needs support to connect to seat
        if ('arm' in comp1['name'].lower() and 'seat' in comp2['name'].lower()):
            return True
        return False
    
    def _create_connector(self, comp1: Dict, comp2: Dict) -> Dict:
        """Create a connecting component between two components"""
        # Get positions
        pos1 = self._get_component_center(comp1)
        pos2 = self._get_component_center(comp2)
        
        # Calculate connector dimensions
        distance = math.sqrt(sum((p2 - p1) ** 2 for p1, p2 in zip(pos1, pos2)))
        
        return {
            'name': f"Connector_{comp1['name']}_{comp2['name']}",
            'operations': [{
                'operation': 'mesh.build_box_mesh',
                'params': {
                    'width': 0.05,  # Standard connector width
                    'depth': 0.05,  # Standard connector depth
                    'height': distance
                },
                'transform': {
                    'location': [
                        (pos1[0] + pos2[0]) / 2,
                        (pos1[1] + pos2[1]) / 2,
                        (pos1[2] + pos2[2]) / 2
                    ],
                    'rotation': self._calculate_connector_rotation(pos1, pos2),
                    'scale': [1, 1, 1]
                }
            }]
        }
    
    def _get_component_center(self, component: Dict) -> List[float]:
        """Get the center position of a component"""
        for op in component.get('operations', []):
            if transform := op.get('transform', {}):
                return transform.get('location', [0, 0, 0])
        return [0, 0, 0]
    
    def _calculate_connector_rotation(self, pos1: List[float], pos2: List[float]) -> List[float]:
        """Calculate rotation angles to align connector between two points"""
        dx, dy, dz = pos2[0] - pos1[0], pos2[1] - pos1[1], pos2[2] - pos1[2]
        
        # Calculate angles (simplified - you might want more complex rotation logic)
        pitch = math.atan2(dz, math.sqrt(dx*dx + dy*dy))
        yaw = math.atan2(dy, dx)
        
        return [pitch, 0, yaw]
    
    def _validate_physical_connections(self, components: List[Dict]) -> List[Dict]:
        """Ensure all connections are physically valid"""
        for i, comp1 in enumerate(components):
            for op1 in comp1.get('operations', []):
                transform1 = op1.get('transform', {})
                params1 = op1.get('params', {})
                
                for comp2 in components[i+1:]:
                    for op2 in comp2.get('operations', []):
                        transform2 = op2.get('transform', {})
                        params2 = op2.get('params', {})
                        
                        if self._are_components_connected(comp1, comp2):
                            self._align_connected_components(op1, op2)
        
        return components
    
    def _align_connected_components(self, op1: Dict, op2: Dict):
        """Adjust transforms to ensure perfect alignment"""
        transform1 = op1.get('transform', {})
        transform2 = op2.get('transform', {})
        params1 = op1.get('params', {})
        params2 = op2.get('params', {})
        
        # Example: Align leg top with table bottom
        if 'height' in params1 and 'height' in params2:
            z1 = transform1['location'][2]
            z2 = transform2['location'][2]
            h1 = params1['height']
            h2 = params2['height']
            
            # Ensure top of one meets bottom of other
            if abs((z1 + h1/2) - (z2 - h2/2)) < 0.1:  # If they're close, make them exact
                transform2['location'][2] = z1 + h1/2 + h2/2 
    
    def _final_position_check(self, components: List[Dict]) -> List[Dict]:
        """Final LLM check to verify and fix all positions and rotations"""
        system_prompt = """You are a 3D furniture expert. Verify and fix component positions and rotations.
        
        CRITICAL RULES:
        1. SUPPORTING STRUCTURES (LEGS/SUPPORTS):
           - Must touch ground (z=0) AND their parent component
           - Must stay WITHIN the bounds of parent component
           - Example: Table legs must not extend beyond table edges
           - For tables/desks: Legs should be inset 2-5cm from edges
           - For cabinets: Side panels must align exactly with top/bottom edges
           - Typical leg inset from edge: 5-10% of total width/depth
        
        2. VERTICAL COMPONENTS:
           - Cabinet sides must be vertical (rotation=[0,0,0])
           - Must align perfectly with edges of horizontal surfaces
           - Vertical supports must not protrude beyond their supported surfaces
           - Support width should be proportional (10-15% of supported width)
        
        3. HORIZONTAL COMPONENTS:
           - Must be perfectly level (rotation=[0,0,0])
           - Shelves/tops must have supports within their boundaries
           - Drawers must fit precisely within frame
           - No overhang unless intentional (e.g., table lip)
        
        4. EXACT CONNECTIONS:
           - Components must have EXACT matching coordinates at joints
           - Example: If table_top.bottom is at z=0.75, leg.top must be at z=0.75
           - No floating components
           - No gaps between connected components
           - Support components must not extend beyond their parent's boundaries
        
        5. PROPORTIONS AND AESTHETICS:
           - Legs should be inset proportionally from edges
           - Support structures should be symmetrically placed
           - Maintain intended design while ensuring structural integrity
           - All supporting elements must stay within parent component bounds
        
        Review each component and fix:
        1. location [x,y,z] (ensuring supports stay within bounds)
        2. rotation [x,y,z]
        3. dimensions and positions relative to parent components
        
        Return corrected components with explanations of changes."""

        try:
            print("\n=== Final Position and Aesthetic Check ===")
            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(components, indent=2)}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            fixes = json.loads(response.choices[0].message.content)
            print("\nApplying final position and proportion fixes:")
            
            # Apply the fixes
            for comp in components:
                if comp['name'] in fixes['components']:
                    fix_data = fixes['components'][comp['name']]
                    for op in comp.get('operations', []):
                        if 'transform' in fix_data:
                            op['transform'] = fix_data['transform']
                        if 'params' in fix_data:
                            op['params'].update(fix_data['params'])
                    print(f"\nFixed {comp['name']}:")
                    print(json.dumps(fix_data, indent=2))
            
            # Verify supporting structures are within bounds
            self._verify_support_bounds(components)
            
            return components
            
        except Exception as e:
            print(f"Error in final position check: {e}")
            return components

    def _verify_support_bounds(self, components: List[Dict]):
        """Verify that supporting structures stay within parent bounds AND touch ground"""
        print("\n=== Verifying Support Structures ===")
        
        # First find all legs/supports and their heights
        support_heights = {}
        for comp in components:
            if any(word in comp['name'].lower() for word in ['leg', 'support', 'side', 'panel']):
                height = comp['operations'][0]['params'].get('height', 0)
                support_heights[comp['name']] = height
        
        # Then adjust parent components to match their supports
        for comp in components:
            parent_transform = comp['operations'][0]['transform']
            parent_params = comp['operations'][0]['params']
            
            # Special handling for chair prongs/star base
            if 'prong' in comp['name'].lower() or ('base' in comp['name'].lower() and 'star' in comp['name'].lower()):
                # Rotate prongs to lie flat
                comp['operations'][0]['transform']['rotation'] = [1.5708, 0, 0]  # 90 degrees in radians around X axis
                
                # If it's a star base with multiple prongs, distribute them radially
                if any(other['name'].startswith(comp['name'].split('_')[0]) for other in components):
                    base_components = [c for c in components if c['name'].startswith(comp['name'].split('_')[0])]
                    num_prongs = len(base_components)
                    
                    for i, prong in enumerate(base_components):
                        angle = (i * 2 * 3.14159) / num_prongs  # Distribute evenly in a circle
                        prong['operations'][0]['transform']['rotation'] = [1.5708, 0, angle]  # Lay flat and rotate around center
                        
                        # Adjust position to form star pattern
                        radius = parent_params.get('width', 0.3) * 0.4  # Use 40% of parent width as radius
                        prong['operations'][0]['transform']['location'] = [
                            radius * np.cos(angle),  # X position
                            radius * np.sin(angle),  # Y position
                            0.01  # Slight lift from ground
                        ]
                
                print(f"\nAdjusted chair prong {comp['name']}:")
                print(f"- Rotated to lie flat")
                print(f"- Position: {comp['operations'][0]['transform']['location']}")
                continue
            
            # Rest of your existing support verification code...
            if any(word in comp['name'].lower() for word in ['top', 'shelf', 'seat', 'base']):
                # Find its supports
                supporting_legs = []
                for support_name, height in support_heights.items():
                    if self._are_components_connected(comp, next(c for c in components if c['name'] == support_name)):
                        supporting_legs.append((support_name, height))
                
                if supporting_legs:
                    # Get max leg height
                    max_leg_height = max(height for _, height in supporting_legs)
                    
                    # Set parent component height to exactly match its legs
                    parent_transform['location'][2] = max_leg_height + parent_params['height']/2
                    
                    print(f"\nAdjusted {comp['name']} to match supports:")
                    print(f"- Support height: {max_leg_height}m")
                    print(f"- New Z position: {parent_transform['location'][2]}m")
                    
                    # Now adjust all legs to exactly match this height
                    for leg_name, _ in supporting_legs:
                        leg = next(c for c in components if c['name'] == leg_name)
                        leg_transform = leg['operations'][0]['transform']
                        leg_params = leg['operations'][0]['params']
                        
                        # Ensure leg reaches from ground to parent
                        leg_params['height'] = max_leg_height
                        leg_transform['location'][2] = max_leg_height/2
                        leg_transform['rotation'] = [0, 0, 0]  # Keep vertical
                        
                        # Keep within parent bounds
                        parent_bounds = self._get_component_bounds(parent_transform, parent_params)
                        inset = min(
                            (parent_bounds['max'][0] - parent_bounds['min'][0]) * 0.1,
                            (parent_bounds['max'][1] - parent_bounds['min'][1]) * 0.1
                        )
                        
                        leg_transform['location'][0] = max(
                            parent_bounds['min'][0] + inset,
                            min(parent_bounds['max'][0] - inset, leg_transform['location'][0])
                        )
                        leg_transform['location'][1] = max(
                            parent_bounds['min'][1] + inset,
                            min(parent_bounds['max'][1] - inset, leg_transform['location'][1])
                        )
                        
                        print(f"\nAdjusted {leg_name}:")
                        print(f"- Height: {max_leg_height}m")
                        print(f"- Position: {leg_transform['location']}") 