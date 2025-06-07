# CS 231N Project

## What we wrote 

We built on top of the Infinigen codebase. We wrote all our files in `cs231n-project/infinigen/primitive_builder`. 
Please check the `agents` folder for each agent's implementation and `full_agent.py` for the full implementation. 
`decomposed_agent.py` and `direct_primitive_agent.py` are incomplete versions of `full_agent.py` used for comparison.

Use case example: Run `python primitive_builder/full_agent.py "DESCRIPTION" "~/Desktop/generated-assets/PRE-VALIDATOR.blend" "~/Desktop/generated-assets/POST-VALIDATOR.blend"` to generate a 
`DESCRIPTION` furniture, with the pre-validator version saved at custom path "~/Desktop/generated-assets/PRE-VALIDATOR.blend" and the post-validator version saved at custom path "~/Desktop/generated-assets/POST-VALIDATOR.blend".
