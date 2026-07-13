# Source retrieval log — 13 July 2026

This log records source-access failures as part of the dataset, rather than
silently treating a browser-readable document as a locally captured source.

## AP63205WU-7

The official Diodes Incorporated PDF initially returned HTTP 403 to a plain
command-line request. A second request with ordinary browser identification and
the official site as referrer returned the 18-page PDF.

- Captured size: 1,226,090 bytes
- SHA-256: ef99daa3789d835bc025dfcb4c605c5c2e6d3e7223e86d40b33e6b497ea5a722
- Repository action: record the hash and locators; do not redistribute the PDF

## PTS815SJM250SMTRLFS

The current three-page Littelfuse/C&K PDF was readable through the browser
review path. Direct byte capture returned HTTP 403, including after ordinary
browser headers were supplied.

- Browser review: completed
- Direct source-byte hash: unknown
- Repository action: record the official URL and exact locators; do not invent
  a hash and do not redistribute the PDF

## Process implication

Source identity, source review, byte capture, hashing, extraction, and
redistribution are separate states. A component record must keep those states
separate so that an access-control response cannot be mistaken for missing
technical evidence or permission to mirror a document.
