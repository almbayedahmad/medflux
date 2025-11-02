# Agent Instructions - Smoke Checklist

Perform these quick checks before handing off a change for review.

- Standards validator: `make validate STAGE=<stage-path>` returns without errors.
- Documentation sync: `make doc-update ...` produces only expected diffs; changelog entries contain real context.
- Git status: only the intended files are modified or staged; hooks ran successfully.
- Runtime sanity: when applicable, execute the stage entry point or a focused unit test to confirm there are no obvious runtime failures.
- Language adherence: confirm all touched content remains in English and avoids forbidden terms such as "loader".
