# hoog-baarlo

Public static site for [Hoog Baarlo](https://hugomeiland.github.io/hoog-baarlo/), with a [Sveltia CMS](https://sveltiacms.app/en/) overlay.

Repo: [hugomeiland/hoog-baarlo](https://github.com/hugomeiland/hoog-baarlo)

## Structure

| Path | Content |
|------|---------|
| `/` | Home (singleton `content/home.yaml`) |
| `/berichten/` | Berichten from `content/berichten/` |
| `/over/` | Over-pagina (`content/pages/over.md`) |
| `/admin/` | Sveltia CMS |

Edits in the CMS are committed to this repository. GitHub Actions then overlays that content onto HTML and deploys GitHub Pages.

## Local preview

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/build.py
python3 -m http.server 4000 --directory _site
```

CMS UI: [http://127.0.0.1:4000/admin/](http://127.0.0.1:4000/admin/)

Sign in with **Sign In Using Access Token**. The prompt includes a GitHub link with the required `repo` scope. Create a token, paste it, and the CMS stores it in the browser.

The blue GitHub OAuth button is disabled on purpose: that flow uses Netlify’s OAuth client, which 404s on GitHub Pages.

## Deploy

GitHub Pages via `.github/workflows/pages.yml`.

Site: **https://hugomeiland.github.io/hoog-baarlo/**

Admin: **https://hugomeiland.github.io/hoog-baarlo/admin/**
