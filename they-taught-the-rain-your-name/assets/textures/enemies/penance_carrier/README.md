# Penance Carrier Texture Slots

Place authored texture exports here. Keep source `.blend`, `.kra`, `.xcf`, ArmorPaint, or Material Maker files in a separate source-art folder if they are too large for Git.

The automated V2 pass writes procedural validation textures to:

```text
assets/textures/enemies/penance_carrier/generated/
```

Those files are runtime placeholders. Replace them with hand-authored 8K hero textures after sculpt, retopo, UV review, and bake cleanup.

## Naming

```text
penance_carrier_body_cloth_basecolor_8k.png
penance_carrier_body_cloth_normal_8k.png
penance_carrier_body_cloth_roughness_8k.png
penance_carrier_body_cloth_ao_8k.png

penance_carrier_house_wood_basecolor_8k.png
penance_carrier_house_wood_normal_8k.png
penance_carrier_house_wood_roughness_8k.png
penance_carrier_house_wood_ao_8k.png

penance_carrier_metal_relics_basecolor_4k.png
penance_carrier_metal_relics_normal_4k.png
penance_carrier_metal_relics_roughness_4k.png
penance_carrier_metal_relics_metallic_4k.png
penance_carrier_metal_relics_ao_4k.png

penance_carrier_paper_decals_basecolor_4k.png
penance_carrier_paper_decals_opacity_4k.png
penance_carrier_paper_decals_roughness_4k.png

penance_carrier_glass_wax_basecolor_2k.png
penance_carrier_glass_wax_normal_2k.png
penance_carrier_glass_wax_roughness_2k.png
penance_carrier_glass_wax_emissive_2k.png
```

## Runtime rule

Keep 8K as the hero/source review target. Export 4K and 2K variants for normal gameplay unless a close-up cinematic truly needs 8K.
