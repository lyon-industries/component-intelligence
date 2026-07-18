# Security policy

Component Intelligence is a public engineering-data and CAD repository, not a
hosted service. Security reports and component-correctness reports follow
different paths so that urgent engineering corrections remain visible without
exposing exploitable details.

## Supported versions

Security fixes are made against the current `main` branch. Fixes are not
backported to earlier commits or copied snapshots. Consumers should pin a
reviewed commit and update deliberately when a relevant correction is released.

## Report a security vulnerability privately

Do not open a public issue for an exploitable problem in repository scripts,
GitHub Actions, dependencies, release artifacts, or the contribution workflow.
Do not publish credentials, tokens, private keys, or a working exploit.

Email `christopher@lyon-industries.no` with the subject
`[component-intelligence security]`. Include, where applicable:

- the affected path and commit SHA
- the security impact and likely attack path
- minimal reproduction steps or a sanitized proof of concept
- tool, operating-system, and dependency versions
- any known mitigations
- your preferred disclosure timeline and attribution

Remove customer, employer, board-design, credential, and other confidential
material before sending. A small synthetic reproduction is preferred. Receipt
will be acknowledged and disclosure will be coordinated after the report can be
reproduced and a safe correction is available. This project does not currently
operate a bug-bounty program.

## Report component or CAD errors publicly

An incorrect exact MPN, source locator, pin map, symbol, footprint, STEP model,
rating, or assembly fact is an engineering-correctness issue rather than a
security vulnerability. Use the **Component error or correction** issue form and
mark anything that could stop fabrication or assembly as `fabrication-stop`.

Do not include confidential designs or proprietary manufacturing data. Reduce
the report to the component, public source, relevant dimensions or pins, and a
sanitized DRC result, screenshot, calculation, or test artifact.

Repository validation and complete-catalog status do not qualify a consuming
circuit, PCB, enclosure, manufacturing process, or regulated product. The
downstream engineer remains responsible for application-specific review and
qualification.
