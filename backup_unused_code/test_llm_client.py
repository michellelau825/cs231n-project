from llm_client import LLMClient

def test_scene_generation():
    # Initialize the client
    client = LLMClient()
    
    # Test with a specific dining room setup
    description = """
    A dining room with:
    - One rectangular wooden dining table (standard size: 180cm x 90cm x 75cm)
    - Four matching wooden dining chairs (standard size: 45cm x 45cm x 90cm)
    - Natural lighting from a large window
    - Modern minimalist style
    """
    
    # Get scene parameters
    scene_params = client.get_scene_parameters(description)
    
    # Print the results in a readable format
    print("\nScene Context:")
    print("-------------")
    for key, value in scene_params['scene_context'].items():
        print(f"{key}: {value}")
    
    print("\nObjects:")
    print("--------")
    for obj in scene_params['objects']:
        print(f"\nType: {obj['type']}")
        for key, value in obj.items():
            if key != 'type':
                print(f"  {key}: {value}")
    
    print("\nLighting:")
    print("---------")
    for key, value in scene_params['lighting'].items():
        print(f"{key}: {value}")
    
    print("\nCamera:")
    print("-------")
    for key, value in scene_params['camera'].items():
        print(f"{key}: {value}")

def test_object_generation():
    """Test object generation with simple prompts"""
    client = LLMClient()
    
    # Test prompts
    prompts = [
        "A simple wooden chair with four legs",
        "A round glass coffee table",
        "A modern metal lamp with a curved stem"
    ]
    
    # Test each prompt
    for prompt in prompts:
        print(f"\nTesting prompt: {prompt}")
        specs = client.analyze_prompt(prompt)
        print("Generated specifications:", specs)

if __name__ == "__main__":
    test_scene_generation()
    test_object_generation() 