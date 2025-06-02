#!/usr/bin/env python3
import os
import sys
import time
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# (1) Make sure our repo root is on sys.path so that `infinigen` and others can be imported.
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Attempt to import FurnitureClassifier—fail loudly if it's not present.
try:
    from primitive_builder.agents.classifier import FurnitureClassifier
except Exception as e:
    print("ERROR: Could not import FurnitureClassifier from primitive_builder.agents.classifier")
    print("Make sure `primitive_builder/agents/classifier.py` is on sys.path and has no errors.")
    raise

def find_blender() -> Optional[Path]:
    """
    Find a Blender executable on the system. Check `which blender` first, then common install paths.
    Return None if not found.
    """
    # Check if `blender` is on PATH
    try:
        blender_path = subprocess.check_output(["which", "blender"], text=True).strip()
        if blender_path:
            return Path(blender_path)
    except subprocess.CalledProcessError:
        pass

    # Common installation locations
    candidates = [
        # macOS
        Path("/Applications/Blender.app/Contents/MacOS/Blender"),
        # Linux
        Path("/usr/bin/blender"),
        Path("/usr/local/bin/blender"),
        # Windows (if ever on Windows)
        Path("C:/Program Files/Blender Foundation/Blender 3.x/blender.exe"),
        Path("C:/Program Files/Blender Foundation/Blender 4.x/blender.exe"),
    ]
    for p in candidates:
        if p.exists():
            return p

    return None

class DirectPrimitiveGenerator:
    """
    -------------
    DRIVER SCRIPT
    -------------
    1) Classify the prompt via FurnitureClassifier.
    2) Call OpenAI to get a JSON spec for primitives.
    3) Write that JSON to disk.
    4) Launch Blender in background, running `new_blendrtojson.py -- <json_path>`.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.classifier = FurnitureClassifier(api_key)

    def generate_primitives(self, prompt: str) -> list:
        """
        Call OpenAI to get a JSON array of component specs.
        Each component must be a dict with at least:
          - "name": str
          - "operations": list of { "operation": str, "params": {...}, "transform": {...} }
        """
        import openai

        system_prompt = """
You are a 3D modeling expert. Convert the following furniture description into a JSON array of primitive operations.
Available Blender primitives:
- bpy.ops.mesh.primitive_cube_add(size, location, rotation)
- bpy.ops.mesh.primitive_cylinder_add(radius, depth, location, rotation)
- bpy.ops.mesh.primitive_uv_sphere_add(radius, location, rotation)
- bpy.ops.mesh.primitive_cone_add(radius1, radius2, depth, location, rotation)
- bpy.ops.mesh.primitive_torus_add(major_radius, minor_radius, location, rotation)
- bpy.ops.mesh.primitive_plane_add(size, location, rotation)

Respond with a JSON array of components. Each component must be:
{
  "name": "component_name",
  "operations": [
    {
      "operation": "bpy.ops.mesh.primitive_cylinder_add",
      "params": {
         "radius": 0.02,
         "depth": 0.4
      },
      "transform": {
         "location": [x, y, z],
         "rotation": [rx, ry, rz],
         "scale": [sx, sy, sz]
      }
    },
    …
  ]
}
Important:
1. The root of the response must be a JSON _array_ of component‐objects.
2. Each component‐object must have `"name"` and `"operations"`.
3. Each operation must have `"operation"`, `"params"`, and `"transform"`.
4. Use only primitives listed above.
5. Do not return any extra keys.
        """.strip()

        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        content = response.choices[0].message.content
        try:
            specs = json.loads(content)
        except json.JSONDecodeError as e:
            print("ERROR: Failed to parse JSON from OpenAI response.")
            print("Raw content was:\n", content)
            raise

        if not isinstance(specs, list):
            raise ValueError(f"Expected a JSON array at top level, but got {type(specs)}")

        # Validate each spec
        validated = []
        for spec in specs:
            if not isinstance(spec, dict):
                raise ValueError(f"Each element of the array must be a dict, but got {type(spec)}")
            if "name" not in spec:
                raise ValueError(f"A component is missing the 'name' field: {spec}")
            if "operations" not in spec or not isinstance(spec["operations"], list):
                raise ValueError(f"A component is missing 'operations' array: {spec}")

            # Filter each operation
            ops = []
            for op in spec["operations"]:
                if not isinstance(op, dict):
                    print("WARNING: Skipping malformed op (not a dict):", op)
                    continue
                if "operation" not in op:
                    print("WARNING: Skipping op with no 'operation' key:", op)
                    continue
                # Ensure transform has all three keys, even if user omitted them
                transform = op.get("transform", {})
                transform.setdefault("location", [0.0, 0.0, 0.0])
                transform.setdefault("rotation", [0.0, 0.0, 0.0])
                transform.setdefault("scale",    [1.0, 1.0, 1.0])

                ops.append({
                    "operation": op["operation"],
                    "params": op.get("params", {}),
                    "transform": transform
                })

            validated.append({
                "name": spec["name"],
                "operations": ops,
                # If your spec includes materials, keep them too
                **({"material": spec["material"]} if "material" in spec else {})
            })

        return validated

    def save_json(self, specs: list, json_path: Path) -> None:
        """
        Write `specs` to `json_path`. Overwrite any existing file.
        """
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(specs, f, indent=2)
        print(f"✓ JSON written to: {json_path}")

    def run_blender(self, json_path: Path) -> Optional[Path]:
        """
        Launch Blender in background, running `new_blendrtojson.py`.
        Return the resulting .blend path if successful, else None.
        """
        blender_path = find_blender()
        if blender_path is None:
            print("ERROR: Could not find Blender on PATH or in common locations.")
            return None

        # The Blender‐side script must live in the primitive_builder directory
        script_path = Path(__file__).parent / "new_blendrtojson.py"
        if not script_path.exists():
            print(f"ERROR: Blender script not found at {script_path}")
            return None

        print(f"→ Using Blender: {blender_path}")
        print(f"→ Using Blender‐side script: {script_path}")
        print(f"→ Passing JSON: {json_path}")

        # Dump the first few lines of the JSON to stdout for debugging:
        snippet = json.dumps(json.loads(json_path.read_text()), indent=2)[:500]
        print("→ JSON snippet (first 500 chars):")
        print(snippet, "\n…")

        cmd = [
            str(blender_path),
            "--background",
            "--python", str(script_path),
            "--", str(json_path)
        ]
        print("→ Running command:")
        print("  ", " ".join(cmd))

        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"← Blender return code: {result.returncode}")
        if result.stderr:
            print("← Blender stderr:")
            print(result.stderr)
        if result.stdout:
            print("← Blender stdout:")
            print(result.stdout)

        if result.returncode != 0:
            print("ERROR: Blender failed. See stderr + stdout above.")
            return None

        blend_path = json_path.with_suffix(".blend")
        if not blend_path.exists():
            print(f"ERROR: Blender finished with code 0 but no .blend at {blend_path}")
            return None

        return blend_path

    def generate(self, prompt: str, output: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Full pipeline:
         1) classify → reject if not furniture
         2) call OpenAI → validated JSON
         3) write JSON to disk
         4) call Blender → produce .blend
        Returns (json_path_str, blend_path_str) or (None, None) if failure.
        """
        print("\n=== Starting DirectPrimitiveGenerator ===")
        print("Input prompt:", prompt)

        # 1) Classification
        print("\n1) Running classifier…")
        classification, explanation = self.classifier.classify(prompt)
        print("  Classification:", classification)
        print("  Explanation:", explanation)
        if classification.lower().strip() == "not a furniture":
            print("  ❌ Rejected: not a piece of furniture. Stopping.")
            return None, None

        # 2) Call OpenAI → JSON specs
        print("\n2) Calling OpenAI to generate primitives…")
        try:
            specs = self.generate_primitives(prompt)
        except Exception as e:
            print("ERROR: Could not generate primitives via OpenAI.")
            raise

        print("  → Received specs (validated):")
        print(json.dumps(specs, indent=2)[:500], "\n…")

        # 3) Write JSON file
        print("\n3) Saving JSON file…")
        if output:
            # If user provided something like `/foo/bar.blend`, replace extension with `.json`
            out = Path(output)
            json_path = out.with_suffix(".json")
        else:
            json_path = Path.cwd() / "generated_primitives.json"
        try:
            self.save_json(specs, json_path)
        except Exception as e:
            print("ERROR: Could not write JSON to disk.")
            raise

        # 4) Launch Blender
        print("\n4) Launching Blender to convert JSON → .blend…")
        blend_path = self.run_blender(json_path)
        if blend_path:
            print("✓ Blender file created at:", blend_path)
            return str(json_path), str(blend_path)
        else:
            return str(json_path), None

def main():
    parser = argparse.ArgumentParser(
        description="Generate 3D furniture from a text description via Blender primitives"
    )
    parser.add_argument("prompt", type=str, help="Furniture description (e.g. 'a wooden stool')")
    parser.add_argument(
        "--output",
        type=str,
        help="Where to write the result; if ends in .blend, JSON will be .json, .blend will be .blend",
        default=None
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only write the JSON file; skip Blender step"
    )
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set in environment")
        sys.exit(1)

    driver = DirectPrimitiveGenerator(api_key)
    try:
        json_path, blend_path = driver.generate(args.prompt, args.output)
    except Exception:
        print("ERROR: Generation pipeline crashed. See traceback above.")
        sys.exit(1)

    if json_path and not args.json_only:
        if blend_path:
            print("\nAll done!\n→ JSON file:  ", json_path, "\n→ BLEND file:", blend_path)
        else:
            print("\nJSON was created at", json_path, "but Blender failed to produce a .blend.")
    elif json_path:
        print("\nJSON was created at", json_path, "— ran with `--json-only` so no .blend was attempted.")
    else:
        print("\nGeneration failed completely.")

if __name__ == "__main__":
    main()
