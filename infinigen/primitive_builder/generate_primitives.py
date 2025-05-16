import sys
import json
import openai

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_primitives.py \"<your prompt>\"")
        sys.exit(1)
    prompt = " ".join(sys.argv[1:])

    system_prompt = (
        "You are a 3D modeling expert. Convert the following description into a series of primitive operations. "
        "Available operations: "
        "- build_prism_mesh: n (sides), r_min, r_max, height. "
        "- bezier_curve: anchors (list of [x,y,z]), resolution. "
        "Respond with a JSON array of operations, each containing: "
        "operation, params, and optional transform (location, rotation, scale)."
    )

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    content = response.choices[0].message.content
    with open("primitives.json", "w") as f:
        f.write(content)
    print("Primitive specs written to primitives.json")

if __name__ == "__main__":
    main() 