# Phase 2 Audit Notes

## Editor-Only Plugin Review

Current project descriptor:

- `PythonScriptPlugin` is enabled in `PenanceDemoUE.uproject`.
- `EditorScriptingUtilities` is enabled in `PenanceDemoUE.uproject`.
- The project has one runtime C++ module: `PenanceDemoUE`.
- There is no project-local `Plugins` directory.

Review result:

- These plugins support editor automation and Python import/setup scripts.
- No plugin version changes were made.
- No project descriptor changes were made.
- No runtime/editor module split was introduced in this phase.

Packaging risk:

- Before a shipping package, verify these editor workflow plugins do not create runtime load assumptions.
- If packaging reports editor-only plugin or module issues, handle that in a dedicated packaging pass instead of changing plugin state during this audit.

Intentionally left untouched:

- `PenanceDemoUE.uproject`
- Unreal assets and maps
- Plugin versions and plugin enablement

## Windows Rendering Defaults Review

Current `DefaultEngine.ini` console variables are configured as low-spec preview defaults:

- `sg.ResolutionQuality=50`
- all major `sg.*Quality` groups are set to `0`
- `r.ScreenPercentage=50`
- motion blur, depth of field, bloom, SSR, and Lumen reflections/diffuse indirect are disabled
- `Interchange.FeatureFlags.Import.FBX=False` is also kept in the same `[ConsoleVariables]` section for import behavior

Review result:

- These settings are Windows-safe from a startup/build perspective.
- They intentionally favor editor responsiveness and low GPU cost over final horror-game visuals.
- They are likely too aggressive for final art, lighting, capture, or shipping review.
- No rendering values were changed in this documentation pass.

Recommended future pass:

- Create named quality profiles or platform-specific config once target hardware is known.
- Re-enable or tune Lumen, shadows, post-process, reflections, and texture quality with visual QA screenshots.
- Keep any final rendering changes separate from build-system and script-safety commits.

Intentionally left untouched:

- `Penance/Config/DefaultEngine.ini` rendering values
- maps, lighting assets, materials, textures, and post-process assets
