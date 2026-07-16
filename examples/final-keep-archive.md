# FINAL_KEEP Archive Discipline Example

Artifact-heavy projects often produce several versions of the same report, image set,
deck, or export. Keep the latest reviewed set easy to find and move the previous set
into a dated archive as one unit.

## Example Layout

```text
FINAL_KEEP/
|-- README.md
|-- maintenance-report.pdf
|-- maintenance-summary.md
`-- archive/
    `-- 2026-06-30-maintenance-review/
        |-- maintenance-report.pdf
        `-- maintenance-summary.md
```

The stable files at the root are the current deliverables. The dated directory contains
the complete set they replaced. `README.md` remains at the root so the project's
artifact policy stays visible.

## Safe Rotation

1. Produce candidate files in a scratch or build location outside `FINAL_KEEP`.
2. Review the candidates for correctness, private data, secrets, and clear file names.
3. Create one archive directory named `YYYY-MM-DD-short-description`.
4. Move the current deliverable set into that directory without changing its contents.
5. Move the reviewed candidates into the root using the stable current file names.
6. Open or render every current artifact, then record the files and checks in
   `HANDOFF.md`.

If promotion fails, the dated directory is the rollback source. Do not delete it while
repairing the current set.

## Naming And Retention Rules

- Use stable, descriptive names for the current files instead of names such as
  `final-v2-really-final.pdf`.
- Date archive directories, not every current artifact.
- Archive a related set together so a report and its summary cannot drift apart.
- Treat archived outputs as immutable. Create a new dated directory for a corrected
  set.
- Follow the repository's retention and large-file policy. `FINAL_KEEP` identifies
  final outputs; it does not require every binary to be committed to Git.

## Handoff Example

```markdown
- Current artifacts: `FINAL_KEEP/maintenance-report.pdf` and
  `FINAL_KEEP/maintenance-summary.md`.
- Archived previous set: `FINAL_KEEP/archive/2026-06-30-maintenance-review/`.
- Verification: opened the PDF, checked the summary links, and scanned both files for
  private data.
```

## Review Checklist

- The root contains only the latest reviewed deliverables and its policy file.
- The previous deliverable set is complete in one dated archive directory.
- Scratch renders, logs, caches, and private inputs are outside `FINAL_KEEP`.
- Current artifacts open successfully and agree with their summaries or manifests.
- `HANDOFF.md` identifies the current set, archived set, and verification performed.
