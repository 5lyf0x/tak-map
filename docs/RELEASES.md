# Release process

Suggested public release flow:

1. Update `CHANGELOG.md`.
2. Run validation:

   ```bash
   ./scripts/validate_package.sh
   ```

3. Build the release ZIP:

   ```bash
   ./scripts/build_package.sh v442
   ```

4. Create a GitHub Release.
5. Attach the ZIP from `dist/`.
6. Copy the relevant `CHANGELOG.md` entry into the release notes.

## Versioning

The app currently carries two version concepts:

- release label: `v1.3.0`
- internal package iteration: `i442`

For public GitHub releases, prefer semantic tags like `v1.3.0`, `v1.2.0`, or `v1.1.1`. The internal package iteration can remain in release notes or ZIP filenames if desired.
