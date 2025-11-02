# Release Process - MedFlux
1. Ensure repo is clean and pre-commit checks pass.
2. Bump version:
   python tools/versioning/bump_version.py patch
3. Commit and tag:
   git add core/versioning/VERSION
   git commit -m "chore(release): bump version to X.Y.Z"
   git tag vX.Y.Z && git push origin main --tags
4. Run GitHub workflow "Release (manual)".
5. Update CHANGELOG.md.
