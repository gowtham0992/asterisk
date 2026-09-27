# Public introduction and separate workspace

The static public page is built from `public_site/index.html` and `site.css`. It introduces the independence ladder, presents the existing saved WSI-Bench measurement, and links to the separately hosted application. The build contains no backend, upload form, analytics, credentials or database. It does include the public derived WSI-Bench result with provenance and retained witness identifiers, already used in the product gallery; it does not include full input tables.

## Build

Run `scripts/build_public_site.py` with the project Python interpreter. Supply `--output` with a fresh directory and `--workspace-url` with the full HTTPS address of the hosted ladder page, including `/static/ladder.html#propose`. Optionally supply `--source-url` once the public source repository exists. URLs containing credentials or unsafe schemes are rejected. Omitting the source URL omits that link rather than creating a fake destination.

The output contains exactly `index.html`, `site.css`, `evidence.json` and `.nojekyll`. Only that output directory should be published to GitHub Pages. Never publish the project root or the broader artifacts directory. Relative asset links support a repository subpath as well as a custom domain. GitHub Pages serves static files and cannot run the Python workspace; the CTA is an ordinary link, not a cross-origin API integration.

A local build was executed with `--output artifacts/public-site-preview --workspace-url http://127.0.0.1:8792/static/ladder.html#propose --allow-localhost`. The localhost exception is explicit and is for preview only. This artifact must be rebuilt with the real hosted URL before publication.

## Verification and remaining decisions

The builder tests cover exact output inventory, counts drawn from the measurement, relative asset paths, rejected stale directories, unsafe URLs, HTML escaping, and explicit localhost opt-in. Desktop and narrow layouts were inspected; width checks at 375px and 768px showed no horizontal overflow. The Open workspace link was followed in the browser and reached the running ladder application on port 8792.

The workspace is deployed at `https://asterisk.gowthamsarveswaran.com/static/ladder.html#propose`. The four production landing-page files are preserved in `site/` on the same repository's `main` branch. The separate site repository was deleted by the owner. The repository is private until closer to submission, so free GitHub Pages is not currently available on this plan; the AWS workspace operates independently.

The previous public deployment from `gh-pages` was verified byte-for-byte (run `36357269553`). That branch is retired as part of consolidation onto `main`. When the owner makes the repository public again, publish only `site/` through a GitHub Pages Actions workflow from `main`; do not recreate a second repository or publish the project root. A real video link can be added when the recording exists.

Documentation checked: [GitHub Pages static publishing](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site). The Pages build does not require Node, a framework or Jekyll.
