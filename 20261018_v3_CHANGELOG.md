# Public release, 18 October 2026, version 3

- Package the reviewed educational component calculations, browser calculator, technical note, source records, exercises and proposed experimental plan as one reproducible release.
- Retain the existing numerical equations, engineering assumptions and missing-input behaviour.
- Use a shared current output prefix across Python exports, browser fixtures and generated pages.
- Rename optional learning metadata to `learner_verification_records` and advance the case metadata schema to version 2. The engineering inputs and calculation results are unchanged.
- Embed the full KaTeX MIT notice in each standalone HTML file that includes the distribution, while retaining its source/integrity manifest and licence file.
- Re-run 117 Python tests, 20 hand/published benchmark comparisons and 155 Python/browser parity vectors successfully. These are numerical implementation checks, separate from physical validation.
