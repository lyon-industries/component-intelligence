# Contributing

Contributions should make a component easier to use correctly, not only easier
to find.

## Minimum record

1. Use one exact orderable manufacturer part number.
2. Link an official source and name its revision or publication date when the
   source provides one.
3. Give every load-bearing fact a page, table, figure, section, or drawing
   locator.
4. Record unknown values as unknown. Do not infer a missing package, pin, model,
   lifecycle state, or rights decision.
5. Keep physical validation separate from source review.
6. Do not add vendor PDFs, images, footprints, or STEP files unless their
   redistribution terms are recorded and compatible with the repository.
7. Add at least one known misuse or integration risk when the part has one.

Run the validator before submitting a change:

    python3 -m pip install -r requirements-dev.txt
    python3 scripts/validate.py

An automated check is not engineering approval. A production claim requires a
named review scope and physical evidence appropriate to the application.
