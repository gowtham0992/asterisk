# Public introduction and protected workspace

Asterisk's read-only introduction is built from `public_site/index.html` and `public_site/site.css`. It presents the retained WSI-Bench measurement, one source witness, the documented patient rule, limits and local setup instructions. It has no upload form, model calls or analytics.

The checked-in build lives in `site/`. The Python app serves it at `/public/` without workspace credentials. Only GET/HEAD for `/public/`, `/public/index.html`, `/public/site.css` and `/public/evidence.json` bypass preview authentication. Unlisted paths, workspace APIs and mutations remain protected.

The public data is the existing derived measurement and retained public witness identifiers. It does not contain full input tables, workspace receipts, credentials or databases. The two technology marks are embedded from the existing attribution artwork during the build; they make no third-party image requests.

## Build

Use the project interpreter and an empty output directory:

```sh
.venv/bin/python -m scripts.build_public_site \
  --output /absolute/path/to/empty-output \
  --workspace-url https://app.example.org/static/ladder.html#receipt
```

Optionally provide `--source-url` with the repository URL. Unsafe schemes, credential-bearing URLs and nonempty output directories are rejected. For a localhost preview, use `--allow-localhost` explicitly.

The output is exactly `index.html`, `site.css`, `evidence.json` and `.nojekyll`. Publish only these build outputs; do not expose the project root. Relative assets support a repository subpath or custom domain. Static hosting cannot run the Python workspace: the call to action links to that separately hosted application.

Copy a reviewed build into `site/` when serving it through the app. The source release includes the four files. Rebuild from the template when changing the destination or adding a source link.

## Verification

The builder checks cover output inventory, metadata-derived counts and witness text, relative assets, HTML escaping, unsafe URLs and stale directories. The route checks enforce the exact public allowlist and continuing protection of workspace pages and APIs. See `tests/test_public_site.py` and `tests/test_release.py`.
