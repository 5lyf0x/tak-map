# Release process

Suggested public release flow:

1. Update `CHANGELOG.md`.
2. Run validation:

   ```bash
   ./scripts/validate_package.sh
   ```

3. Build the release ZIP:

   ```bash
   ./scripts/build_package.sh v324
   ```

4. Create a GitHub Release.
5. Attach the ZIP from `dist/`.
6. Copy the relevant `CHANGELOG.md` entry into the release notes.

## Versioning

The app currently carries two version concepts:

- release label: `v1.1.0`
- internal package iteration: `v324`

For public GitHub releases, prefer semantic tags like `v1.1.0`, `v1.1.1`, or `v1.2.0`. The internal package iteration can remain in release notes or ZIP filenames if desired.
