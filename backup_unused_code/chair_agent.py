import sys
import openai
import json

def get_primitive_specs(prompt: str) -> str:
    client = openai.OpenAI()
    system_prompt = """You are a 3D modeling expert. Convert the following description into a series of primitive operations.\nAvailable operations:\n- build_prism_mesh: Creates prismatic mesh. Parameters: n (sides), r_min, r_max, height\n- bezier_curve: Creates a curved shape. Parameters: anchors (list of [x,y,z] points), resolution\n\nRespond with a JSON array of operations, each containing:\n- operation: one of the available operations\n- params: parameters for the operation\n- transform: optional transformation parameters (location, rotation, scale)\n"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m infinigen.assets.objects.seating.chairs.agents.chair_agent \"<your prompt>\"")
        sys.exit(1)
    prompt = " ".join(sys.argv[1:])
    specs = get_primitive_specs(prompt)
    with open("primitives.json", "w") as f:
        f.write(specs)
    print("Primitive specs written to primitives.json") 