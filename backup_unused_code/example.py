import bpy
from infinigen.primitive_builder.primitive_builder import ProceduralSceneBuilder
from infinigen.primitive_builder.llm_client import LLMClient

def create_scene_from_description(description: str):
    """Create a scene from a natural language description"""
    
    # Initialize the LLM client and scene builder
    llm_client = LLMClient()
    builder = ProceduralSceneBuilder(llm_client)
    
    # Create the object
    obj = builder.build_from_description(description)
    
    # Set up the scene
    bpy.context.scene.camera.location = (5, -5, 3)
    bpy.context.scene.camera.rotation_euler = (0.9, 0, 0.8)
    
    # Add lighting
    light_data = bpy.data.lights.new(name="Light", type='SUN')
    light_data.energy = 5.0
    light_obj = bpy.data.objects.new(name="Light", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.rotation_euler = (0.6, 0.8, -0.3)
    
    return obj

if __name__ == "__main__":
    # Example: Create a modern chair
    description = """
    Create a modern wooden chair with:
    - A curved, ergonomic backrest
    - A slightly contoured seat
    - Four straight, tapered legs
    - Clean, minimalist design
    """
    
    obj = create_scene_from_description(description)
    print(f"Created object: {obj.name}")
    
    # Example: Create a coffee table
    description = """
    Create a minimalist glass coffee table with:
    - A rectangular glass top
    - Two curved metal legs
    - Modern, floating appearance
    """
    
    obj = create_scene_from_description(description)
    print(f"Created object: {obj.name}")
    
    # Example: Create a window
    description = """
    Create a traditional wooden window with:
    - Four panes of glass
    - Wooden mullions
    - Classic arch top
    - White painted frame
    """
    
    obj = create_scene_from_description(description)
    print(f"Created object: {obj.name}") 