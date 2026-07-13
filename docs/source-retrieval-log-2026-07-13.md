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

## Catalog expansion

The expansion from two to 20 records used official manufacturer documents
only. Fourteen of the 18 new sources were captured as PDF bytes and hashed.
Four were readable through the browser review path but command-line capture
was blocked or terminated by the publisher's delivery system.

| Exact MPN | Publisher | Retrieval state |
| --- | --- | --- |
| AO3400A | Alpha & Omega Semiconductor | Captured and hashed |
| MAX3485ESA+ | Analog Devices | Browser reviewed; byte capture blocked |
| BME280 | Bosch Sensortec | Captured and hashed |
| ESP32-C3-WROOM-02-N4 | Espressif Systems | Captured and hashed |
| 24LC256-I/SN | Microchip Technology | Captured and hashed |
| ATtiny85-20SU | Microchip Technology | Captured and hashed |
| MCP73831T-2ACI/OT | Microchip Technology | Browser reviewed; byte capture blocked |
| BAT54C,215 | Nexperia | Captured and hashed |
| STM32C011F6P6TR | STMicroelectronics | Browser reviewed; byte capture blocked |
| USBLC6-2SC6 | STMicroelectronics | Browser reviewed; byte capture blocked |
| ADS1115IDGSR | Texas Instruments | Captured and hashed |
| INA219AIDCNR | Texas Instruments | Captured and hashed |
| LM358DR | Texas Instruments | Captured and hashed |
| NE555DR | Texas Instruments | Captured and hashed |
| PCA9306DCTR | Texas Instruments | Captured and hashed |
| SN74LVC1G17DBVR | Texas Instruments | Captured and hashed |
| TLV75533PDBVR | Texas Instruments | Captured and hashed |
| TPS62162DSGR | Texas Instruments | Captured and hashed |

The PDFs are not stored in this repository. Each component record carries the
source URL, revision when stated, exact locators, retrieval state, byte size,
and SHA-256 when capture succeeded.
