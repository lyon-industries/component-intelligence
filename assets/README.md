# Repository artwork provenance

## Social preview

`component-intelligence-social-preview.png` is a 1280 × 640 repository and
social-preview image prepared on 2026-07-18.

- The charcoal geometric background is AI-generated decorative artwork. It is
  not a circuit board, product render, or engineering-test artifact.
- The INA219AIDR pad map is drawn from the canonical coordinates and pin names
  in `components/ti/INA219AIDR/component.json`.
- The package view is rendered from the repository's generated nominal
  `INA219AIDR.step` asset.
- The displayed catalog counts come from the validated 2026-07-18 launch state.
- No physical build, assembly, measurement, or certification is implied.

The final PNG is quantized to 128 colors and is 363 KB, below GitHub's 1 MB
social-preview recommendation.

## Component catalog graph

`component-catalog-graph.svg` is a deterministic 1600 × 900 README image
generated from repository metadata.

- Device nodes come only from complete-tier `components/*/*/component.json`
  records and display each canonical exact MPN once.
- Category labels are the canonical `classification.category` values.
- The five engineering domains are a maintained presentation taxonomy used to
  make the graph readable; they are not additional schema fields.
- Candidate devices are excluded from the graph. Only their quarantined count
  is shown.
- The current Lyon Industries palette and locked Helvetica Neue/mono type roles
  govern the composition. Propellant appears once as the repository ignition;
  categories remain legible by labels and hierarchy rather than colour coding.
- The graph contains no stock or AI-generated imagery. Its visible technical
  content is derived from the canonical metadata.
- The image claims no physical validation, circuit approval, or production
  qualification.

Regenerate it with `python3 scripts/build_catalog.py` or directly with
`python3 scripts/generate_component_graph.py`. The checked-in SVG must not be
edited by hand.
