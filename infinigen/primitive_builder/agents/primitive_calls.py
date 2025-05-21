import openai
from typing import Dict, List
import json
from pathlib import Path
from .context_provider import ContextProvider
from .validator import ComponentValidator
from .materials_agent import MaterialsAgent

class PrimitiveGenerator:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.primitives_dir = Path.home() / "Desktop" / "generated-assets" / "primitives"
        self.primitives_dir.mkdir(parents=True, exist_ok=True)
        self.context_provider = ContextProvider()
        self.validator = ComponentValidator(api_key)
        self.materials_agent = MaterialsAgent(api_key)
        
    def generate(self, components: Dict) -> List[Dict]:
        print("\n=== Starting Primitive Generation ===")
        print("Input components:", json.dumps(components, indent=2))
        
        # Get factory context
        print("\n=== Loading Factory Examples ===")
        factory_context = self.context_provider.get_factory_context()
        print("\nFactory Context Loaded:")
        print(factory_context)
        
        # Add context to system prompt
        system_prompt = """You are a 3D modeling expert. Convert each component into optimal operations, respecting quantities from the decomposition.

CRITICAL ORDERING RULES:
1. Always start with ground-touching components (legs, base supports)
2. Then build upward components that connect to them (the locations must connect, they must touch, this is extremely important)
3. Finally add decorative elements (handles, trim)

Example Order for Chair:
1. Legs (ground up)
2. Seat base (connects to legs)
3. Back support posts (connects to seat)
4. Seat back (connects to posts)
5. Armrest supports (connects to seat)
6. Armrests (connects to supports)

Example Order for Cabinet:
1. Base supports/legs
2. Bottom panel
3. Side panels (connect to bottom)
4. Back panel
5. Shelves (connect to sides)
6. Drawer tracks
7. Drawers
8. Drawer fronts
9. Handles/knobs
10. Top panel

FACTORY EXAMPLES FOR REFERENCE:
""" + factory_context + """

AVAILABLE FUNCTIONS (Choose the best for each component):

From infinigen/assets/utils/mesh.py:
- mesh.build_box_mesh(width=1.0, depth=1.0, height=1.0)  # Perfect for flat surfaces and straight edges
- mesh.build_plane_mesh(width=1.0, depth=1.0)  # For thin flat surfaces
- mesh.build_prism_mesh(n=6, r_min=1.0, r_max=1.5, height=0.3, tilt=0.3)  # For angular shapes
- mesh.build_cylinder_mesh(radius=1.0, height=2.0, segments=32)  # For perfect cylinders
- mesh.build_cone_mesh(radius=1.0, height=2.0, segments=32)  # For conical shapes
- mesh.build_sphere_mesh(radius=1.0, segments=32, rings=16)  # For spherical shapes
- mesh.build_torus_mesh(major_radius=1.0, minor_radius=0.25, major_segments=32, minor_segments=16)  # For ring shapes, the center is hollow
- mesh.dissolve_degenerate(obj)  # Cleanup mesh
- mesh.dissolve_limited(obj)  # Cleanup mesh
- mesh.duplicate_face(obj, face_idx)  # For detailed parts
- mesh.duplicate_vertices(obj)  # For mesh manipulation
- mesh.ensure_loop_order(obj)  # Fix mesh topology
- mesh.extrude_and_move(obj, face_idx, offset)  # Precise extrusion
- mesh.extrude_edges(obj, edge_idx)  # Edge detail
- mesh.extrude_faces(obj)  # Add depth
- mesh.extrude_region_and_move(obj, face_idx, offset)  # Complex extrusion
- mesh.face_by_verts(obj, vert_idxs)  # Create custom faces
- mesh.flip_normals(obj)  # Fix face orientation
- mesh.inset_faces(obj, face_idx)  # Add detail to faces
- mesh.merge_by_distance(obj)  # Clean up vertices
- mesh.recalc_normals(obj)  # Fix shading
- mesh.remove_doubles(obj)  # Clean up mesh
- mesh.remove_unused_vertices(obj)  # Optimize mesh
- mesh.subdivide_edges(obj, edge_idx)  # Add detail
- mesh.triangulate(obj)  # Improve mesh quality
- mesh.snap_mesh(obj, eps=1e-3)  # Clean up mesh
- mesh.prepare_for_boolean(obj)  # Prepare for boolean operations
- mesh.face_area(obj)  # Calculate face area
- mesh.centroid(obj)  # Find center
- mesh.longest_ray(obj, obj_, direction)  # For ray calculations
- mesh.treeify(obj)  # Create tree structure
- mesh.fix_tree(obj)  # Fix tree topology
- mesh.longest_path(obj)  # Find longest path
- mesh.bevel(obj, width)  # Add bevels
- mesh.canonicalize_ls(line)  # Clean up line strings
- mesh.canonicalize_mls(mls)  # Clean up multi-line strings
- mesh.separate_selected(obj, face=False)  # Separate parts

From infinigen/assets/utils/draw.py:
- draw.spin(anchors, vector_locations=(), axis=(0,0,1))  # For circular shapes
- draw.shape_by_angles(obj, angles, scales=None)  # For complex profiles
- draw.surface_from_func(fn, div_x=16, div_y=16)  # For curved surfaces
- draw.bezier_curve(anchors, to_mesh=True)  # For smooth curves
- draw.remesh_fill(obj, resolution=0.005)  # Improve mesh quality
- draw.cut_plane(obj, cut_center, cut_normal)  # For precise cuts

From infinigen/assets/utils/object.py:
- object.center(obj)  # Center object
- object.origin2lowest(obj)  # Move origin to bottom
- object.join_objects(objects)  # Combine parts
- object.new_cube(**kwargs)  # Simple cube
- object.new_cylinder(**kwargs)  # Simple cylinder
- object.new_circle(**kwargs)  # For circular parts
- object.new_plane(**kwargs)  # For flat surfaces

Blender Operations (use only when needed):
- bpy.ops.object.modifier_add(type='BEVEL')  # Smooth edges
- bpy.ops.object.modifier_add(type='SUBSURF')  # Smooth surfaces
- bpy.ops.object.shade_smooth()  # Improve appearance

OPTIMIZATION STRATEGY:
1. Start with the most appropriate base mesh function:
   - mesh.build_box_mesh for rectangular parts
   - mesh.build_cylinder_mesh for circular columns
   - mesh.build_sphere_mesh for rounded elements
   - mesh.build_prism_mesh for angular shapes
   
2. Apply mesh operations in this order:
   a) Create base shape
   b) Apply extrusions or modifications
   c) Clean up (merge_by_distance, remove_doubles)
   d) Fix normals and topology
   e) Add detail (bevel, subdivide)
   f) Final cleanup and preparation

SPATIAL CONSTRAINTS:
1. Table/Chair Tops:
   - Must be perfectly horizontal (rotation [0,0,0])
   - Standard heights: Tables 0.7-0.8, Chairs 0.4-0.45
   - Thickness: 0.02-0.05 units
   - Surface must be flat and level

2. Legs:
   - Must be FLUSH with the top surface (no protrusion)
   - Must reach exactly to ground (y=0)
   - Must be vertical unless design specifies otherwise
   - Must be symmetrically placed
   - Must be properly inset from edges (typically 0.05-0.1 units)
   - For tables: position at corners
   - For chairs: position for stability

Example (Table Leg Done Right):
[
    {
        "operation": "mesh.build_box_mesh",  # Base leg shape
        "params": {
            "width": 0.06,
            "depth": 0.06,
            "height": 0.75  # Exactly table_height
        },
        "transform": {
            "location": [0.57, 0.37, 0.375],  # Positioned under top surface
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1]
        }
    },
    {
        "operation": "bpy.ops.object.modifier_add",  # Add bevel for realism
        "params": {"type": "BEVEL"}
    },
    {
        "operation": "bpy.ops.object.shade_smooth",  # Improve appearance
        "params": {}
    }
]

COMPONENT-BASED STRUCTURE:
Each component from the decomposition must have its own set of operations. Output format:

{
    "components": [
        {
            "name": "Table Top",
            "operations": [
                {
                    "operation": "mesh.build_box_mesh",
                    "params": {
                        "width": 1.2,
                        "depth": 0.8,
                        "height": 0.03
                    },
                    "transform": {
                        "location": [0, 0, 0.75],
                        "rotation": [0, 0, 0],
                        "scale": [1, 1, 1]
                    }
                },
                {
                    "operation": "bpy.ops.object.shade_smooth",
                    "params": {}
                }
            ]
        },
        {
            "name": "Table Leg 1",
            "operations": [
                {
                    "operation": "mesh.build_cylinder_mesh",
                    "params": {
                        "radius": 0.03,
                        "height": 0.72,
                        "segments": 16
                    },
                    "transform": {
                        "location": [0.57, 0.37, 0.36],
                        "rotation": [0, 0, 0],
                        "scale": [1, 1, 1]
                    }
                }
            ]
        }
    ]
}

HANDLING COMPONENT QUANTITIES:
1. Check the "quantity" field for each component
2. For quantity > 1:
   - Create ONE base component specification
   - Duplicate it exactly "quantity" times
   - ONLY modify position/rotation for each instance
   - ALL other parameters must be identical
   - Name format: "{Component}_{Number}" (e.g., "Table_Leg_1")

Example - Table with 4 Identical Legs:
{
    "components": [
        {
            "name": "Table_Top",
            "operations": [
                {
                    "operation": "mesh.build_box_mesh",
                    "params": {"width": 1.2, "depth": 0.8, "height": 0.03},
                    "transform": {"location": [0, 0, 0.75], "rotation": [0, 0, 0], "scale": [1, 1, 1]}
                }
            ]
        },
        # IDENTICAL LEGS - Note how only location changes
        {
            "name": "Table_Leg_1",
            "operations": [
                {
                    "operation": "mesh.build_cylinder_mesh",
                    "params": {  # IDENTICAL params for all legs
                        "radius": 0.03,
                        "height": 0.72,
                        "segments": 16
                    },
                    "transform": {"location": [0.57, 0.37, 0.36], "rotation": [0, 0, 0], "scale": [1, 1, 1]}
                }
            ]
        },
        {
            "name": "Table_Leg_2",
            "operations": [  # EXACT SAME operations
                {
                    "operation": "mesh.build_cylinder_mesh",
                    "params": {  # IDENTICAL params
                        "radius": 0.03,
                        "height": 0.72,
                        "segments": 16
                    },
                    "transform": {"location": [-0.57, 0.37, 0.36], "rotation": [0, 0, 0], "scale": [1, 1, 1]}
                }
            ]
        }
        ... # Legs 3 and 4 with same operations, different positions
    ]
}

QUANTITY VALIDATION RULES:
1. Number of generated components MUST match quantities from decomposition
2. For quantity > 1:
   - All instances must have identical operations
   - All instances must have identical parameters
   - Only transform values may differ
   - Names must follow sequential numbering
3. Spatial arrangements must match decomposition:
   - "mirrored_positions" -> symmetrical placement
   - "radial_arrangement" -> circular placement
   - "corner_positions" -> at corners with proper insets
   - "distributed" -> evenly spaced

VALIDATION RULES:
1. Each component from step 3 must have exactly one entry in the components list
2. Component names must match those from the decomposition
3. Each component must have at least one operation
4. Operations must be properly sequenced (create mesh first, then modify)
5. All spatial constraints still apply
6. Components must be properly connected in 3D space

VALIDATION RULES FOR MULTIPLE COMPONENTS:
1. Each instance must be a separate component entry
2. All parameters except position/rotation must be identical
3. Names must be sequentially numbered
4. Positions must be symmetrical where appropriate
5. All instances must maintain proper spatial relationships
6. Scale should remain consistent across instances
7. Material properties (if any) should be identical

SPATIAL ARRANGEMENT PATTERNS:
1. Linear Arrays: Equal spacing along an axis
2. Circular Arrays: Equal angles around a center
3. Grid Patterns: Regular spacing in both X and Y
4. Symmetrical Pairs: Mirrored across an axis
5. Radial Patterns: Spokes around a central point

CONNECTION DIMENSION RULES:
1. Supporting components (legs, posts, etc.) must have EXACT dimensions:
   - height = distance from ground to supported component's bottom
   - For Table Leg example:
     if table_top.location.z = 0.75 and table_top.height = 0.03
     then leg.height MUST = 0.75 (to reach from ground to table bottom)

2. Connecting components (crossbars, supports) must span EXACT distance:
   - length = distance between connection points
   - For Crossbar example:
     if leg1.location = [0.57, 0.37, 0] and leg2.location = [-0.57, 0.37, 0]
     then crossbar.length MUST = 1.14 (exact distance between legs)

3. Nested components must have precise clearances:
   - outer.dimensions > inner.dimensions
   - clearance gaps must be specified and consistent
   - Example: drawer inside cabinet must have exact width/depth to slide

4. Stacked components must align exactly:
   - bottom_component.top_face = top_component.bottom_face
   - shared dimensions must match (width/depth for vertical stacking)
   - Example: table leg height must exactly match table top bottom surface

5. Dimension Calculation Rules:
   - Always calculate exact distances between connection points
   - Use vector math for angled connections
   - Account for component thickness in calculations
   - No gaps or overlaps allowed unless specified
   - Maintain symmetry for identical components

Example - Crossbar between Table Legs:
{
    "name": "Table_Crossbar",
    "operations": [
        {
            "operation": "mesh.build_box_mesh",
            "params": {
                "width": 1.14,  # EXACT distance between legs
                "depth": 0.03,
                "height": 0.03
            },
            "transform": {
                "location": [0, 0.37, 0.2],  # Centered between legs
                "rotation": [0, 0, 0],
                "scale": [1, 1, 1]
            },
            "connections": [
                {
                    "type": "end_mount",
                    "target": "Table_Leg_1",
                    "point": [0.57, 0.37, 0.2]
                },
                {
                    "type": "end_mount",
                    "target": "Table_Leg_2",
                    "point": [-0.57, 0.37, 0.2]
                }
            ]
        }
    ]
}

CRITICAL COMPONENT COMPLETENESS RULES:
1. EVERY component from the decomposer MUST be included:
   - Check decomposer output carefully
   - Create operations for EVERY listed component
   - No components can be skipped or omitted
   - Verify final component count matches decomposer exactly

2. Component Matching Requirements:
   - Names must match decomposer exactly
   - Quantities must match decomposer exactly
   - All properties must be implemented
   - All connections must be specified
   - All spatial relationships must be maintained

3. Validation Checklist:
   - ✓ Count total components from decomposer
   - ✓ Create matching number of components
   - ✓ Verify each component name exists
   - ✓ Check all quantities are correct
   - ✓ Confirm all connections are specified

Example - Complete Component Coverage:
Decomposer Input:
{
    "components": [
        {"name": "Table_Top", "quantity": 1},
        {"name": "Table_Leg", "quantity": 4},
        {"name": "Cross_Support", "quantity": 2}
    ]
}

Required Output (ALL components included):
{
    "components": [
        {"name": "Table_Top", ...},
        {"name": "Table_Leg_1", ...},
        {"name": "Table_Leg_2", ...},
        {"name": "Table_Leg_3", ...},
        {"name": "Table_Leg_4", ...},
        {"name": "Cross_Support_1", ...},
        {"name": "Cross_Support_2", ...}
    ]
}

VERIFICATION REQUIREMENT:
Before outputting, verify that EVERY SINGLE component from the decomposer has corresponding operations defined. NO EXCEPTIONS.

Output ONLY valid JSON with no additional text."""

        try:
            print("\nCalling GPT-4...")
            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(components)}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            print("\nGPT Response:", content)
            
            try:
                parsed = json.loads(content)
                if "components" not in parsed:
                    print("Error: Response missing 'components' list")
                    return []
                
                # Validate component structure
                components_list = parsed['components']
                if not isinstance(components_list, list):
                    print("Error: 'components' is not a list")
                    return []
                
                # Validate and fix component connections
                print("\n=== Starting Component Validation ===")
                validated_components = self.validator.validate_and_fix(components_list)
                
                if validated_components:
                    print(f"\nSuccessfully validated {len(validated_components)} components")
                    print("Final component structure with all connections:")
                    print(json.dumps(validated_components, indent=2))
                    
                    # Write the validated components to a file for debugging
                    import os
                    from pathlib import Path
                    output_dir = Path.home() / "Desktop" / "generated-assets"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_file = output_dir / "latest_validated_components.json"
                    
                    with open(output_file, "w") as f:
                        json.dump({"components": validated_components}, f, indent=2)
                    print(f"\nWrote validated components to: {output_file}")
                    
                    # Assign materials to validated components
                    components_with_materials = self.materials_agent.assign_materials(validated_components)
                    
                    if components_with_materials:
                        print(f"\nSuccessfully generated and validated {len(components_with_materials)} components with materials")
                        return components_with_materials
                    else:
                        print("\nError: No components generated")
                        return []
                else:
                    print("\nValidation failed, returning original components")
                    return components_list
                
            except json.JSONDecodeError as e:
                print(f"\nError parsing JSON: {str(e)}")
                print("Content was:", repr(content))
                return []
            
        except Exception as e:
            print(f"\nError in primitive generation: {e}")
            return []

    def _validate_connections(self, components: List[Dict]) -> List[Dict]:
        """Ensure all components are properly connected and grounded"""
        
        # Find all components that need ground contact (legs, bases, etc.)
        ground_components = []
        supported_components = set()
        supporting_pairs = []  # Track which components support others
        
        # First pass: identify components and their relationships
        for comp in components:
            if self._needs_ground_contact(comp):
                ground_components.append(comp)
            
            # Track what components are supported
            ops = comp.get('operations', [])
            for op in ops:
                transform = op.get('transform', {})
                if transform.get('location'):
                    # If it's above ground and not a ground component, it needs support
                    if transform['location'][2] > 0 and comp not in ground_components:
                        supported_components.add(comp['name'])
                        
                        # Find its supporting component
                        for support in ground_components:
                            if self._is_supporting(support, comp):
                                supporting_pairs.append((support, comp))
        
        # Second pass: ensure ground components reach the floor
        for comp in ground_components:
            ops = comp.get('operations', [])
            for op in ops:
                transform = op.get('transform', {})
                params = op.get('params', {})
                if transform.get('location'):
                    # Find the component this supports (if any)
                    supported_comp = next((pair[1] for pair in supporting_pairs if pair[0] == comp), None)
                    
                    if supported_comp:
                        # Get the supported component's bottom z-coordinate
                        supported_ops = supported_comp.get('operations', [])
                        for supported_op in supported_ops:
                            supported_transform = supported_op.get('transform', {})
                            supported_params = supported_op.get('params', {})
                            if supported_transform and supported_params:
                                # Calculate the actual bottom of the supported component
                                supported_z = supported_transform['location'][2]
                                supported_height = supported_params.get('height', 0)
                                bottom_z = supported_z - (supported_height / 2)
                                
                                # Update leg height to reach exactly to the bottom
                                height = bottom_z
                                params['height'] = height
                                transform['location'] = [
                                    transform['location'][0],
                                    transform['location'][1],
                                    height / 2  # Center point should be half height
                                ]
                    else:
                        # Standard ground component handling
                        height = transform['location'][2] * 2
                        params['height'] = height
                        transform['location'][2] = height / 2
        
        # Third pass: ensure supported components have connections
        for comp in components:
            if comp['name'] in supported_components:
                self._ensure_support_connections(comp, components)
        
        return components

    def _is_supporting(self, support_comp: Dict, target_comp: Dict) -> bool:
        """Check if one component is supporting another"""
        support_ops = support_comp.get('operations', [])
        target_ops = target_comp.get('operations', [])
        
        for support_op in support_ops:
            support_transform = support_op.get('transform', {})
            if not support_transform:
                continue
                
            for target_op in target_ops:
                target_transform = target_op.get('transform', {})
                target_params = target_op.get('params', {})
                if not (target_transform and target_params):
                    continue
                
                # Check if components are aligned vertically
                if abs(support_transform['location'][0] - target_transform['location'][0]) < 0.1 and \
                   abs(support_transform['location'][1] - target_transform['location'][1]) < 0.1:
                    return True
        
        return False

    def _needs_ground_contact(self, component: Dict) -> bool:
        """Determine if component should contact the ground"""
        name_lower = component['name'].lower()
        ground_keywords = ['leg', 'base', 'stand', 'foot', 'support', 'pedestal']
        return any(keyword in name_lower for keyword in ground_keywords)

    def _ensure_support_connections(self, component: Dict, all_components: List[Dict]) -> None:
        """Ensure component has proper support connections"""
        ops = component.get('operations', [])
        for op in ops:
            transform = op.get('transform', {})
            if transform.get('location'):
                z_height = transform['location'][2]
                
                # Add connection points if not present
                if 'connections' not in op:
                    op['connections'] = []
                
                # Find supporting components
                for support in all_components:
                    if self._needs_ground_contact(support):
                        support_ops = support.get('operations', [])
                        for support_op in support_ops:
                            support_transform = support_op.get('transform', {})
                            if support_transform.get('location'):
                                # If support is below this component, add connection
                                if abs(support_transform['location'][0] - transform['location'][0]) < 0.1 and \
                                   abs(support_transform['location'][1] - transform['location'][1]) < 0.1:
                                    op['connections'].append({
                                        "type": "surface_mount",
                                        "target": support['name'],
                                        "point": transform['location'],
                                        "orientation": "vertical",
                                        "flush": True
                                    })
