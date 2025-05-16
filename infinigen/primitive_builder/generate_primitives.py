import sys
import json
import os
import openai
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_primitives.py \"<your prompt>\"")
        sys.exit(1)
    prompt = " ".join(sys.argv[1:])

    # Get API key from environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it using: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)

    system_prompt = (
        "You are a 3D modeling expert. Convert the following description into a series of primitive operations. "
        "Available operations from Infinigen: "
        "- build_prism_mesh: n (sides), r_min, r_max, height, tilt. "
        "- build_convex_mesh: n (sides), height, tilt. "
        "- build_cylinder_mesh: radius, height, segments. "
        "- build_cone_mesh: radius, height, segments. "
        "- build_sphere_mesh: radius, segments, rings. "
        "- build_torus_mesh: major_radius, minor_radius, major_segments, minor_segments. "
        "- build_box_mesh: width, depth, height. "
        "- build_plane_mesh: width, depth. "
        "- bezier_curve: anchors (list of [x,y,z]), vector_locations (list), resolution, to_mesh. "
        "- align_bezier: anchors (list of [x,y,z]), axes (list), scale (list), vector_locations (list), resolution, to_mesh. "
        "Respond with a JSON array of operations, each containing: "
        "operation, params, and optional transform (location, rotation, scale)."
    )

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    content = response.choices[0].message.content

    # Create desktop/generated-assets folder if it doesn't exist
    desktop_path = Path.home() / "Desktop" / "generated-assets"
    desktop_path.mkdir(exist_ok=True)

    # Save primitives.json to desktop/generated-assets
    output_path = desktop_path / "primitives.json"
    with open(output_path, "w") as f:
        f.write(content)
    print(f"Primitive specs written to {output_path}")

if __name__ == "__main__":
    main() 