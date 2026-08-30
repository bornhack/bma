# BMA documentation

This directory describes the repository as it exists on 30 August 2026. It is
implementation documentation, not a target design or a refactoring proposal.

- [Architecture overview](architecture/overview.md) — application boundaries,
  data flow, storage, and the dependency/Django 6 status report.
- [File and image model](architecture/file-and-image-model.md) — the persisted
  media, rendition, and job relationships.
- [Image processing](architecture/image-processing.md) — how BMA creates and
  accepts client-produced media work.
- [Frontend](architecture/frontend.md) — Django templates, custom template
  tags, JavaScript, and media presentation.

The code is the source of truth. Paths in these documents are repository-root
relative.
