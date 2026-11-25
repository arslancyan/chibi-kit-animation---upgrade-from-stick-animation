# Chibi characters

## Base body (shared by every character)
Polished flat-colour 2.5D cutout, soft rounded forms, thick dark outline, about 3.5 to 4 heads tall.
Parts, each its own transparent PNG layer: head (with ears), torso, upper arm L/R, forearm+hand L/R, upper leg L/R,
lower leg+foot L/R.
Joints: head, neck, shoulder L/R, elbow L/R, wrist L/R, hip L/R, knee L/R, ankle L/R.
Pivot points are stored in `assets/base_body/rig.json` (to be created from the base sheet).

## Per-character layers (added on top of the base body)
- Face: eyes, brows, mouth, with 8 expressions: neutral, talking, smirk, happy, surprised, annoyed, thinking, laugh.
- Hair (front, back, side variants), clothes (top, bottom, shoes), accessories (watch etc).
- Head shape variant for supporting cast: rounded square, round, oval, wide, squircle, bean, hexagon, teardrop.

## Style rules
- Outline weight constant across the cast; flat fill plus one shadow tone and a rim light matching scene light.
- Skin and face stay readable in every scene (light tint from scene is allowed, never a colour cast that hides the expression).
- New cast per video, and a design sheet is shown for approval before building.
- Lead character: the user's character (sheets live in `assets/`), others are built from the base body.
