# Security

Review this checklist before publishing the repository or creating a release.

## Never commit

- TAK client certificates or private keys
- HTTPS CA/server certificates or private keys
- `.env` files
- runtime config files from `/etc/` or `/var/lib/`
- local data exports that reveal sensitive locations
- map packages or mission exports from real operations
- screenshots showing private IPs, callsigns, server names, or credentials
- logs with usernames, tokens, session cookies, IPs, or service output

## Recommended pre-commit checks

```bash
git status --short
git diff --stat
git diff --cached --stat
```

Search for common secret patterns:

```bash
grep -RInE 'PRIVATE KEY|BEGIN RSA|BEGIN EC|password|secret|token|api[_-]?key' . \
  --exclude-dir=.git --exclude-dir=assets --exclude='*.png' --exclude='*.zip'
```

## Runtime certs

Generated certs belong on the installed system only. They are ignored by `.gitignore` and should not be added to source control.
