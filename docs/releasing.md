# Releasing

For maintainers. PDLt is published to PyPI as [`pdl-taskmaster`](https://pypi.org/project/pdl-taskmaster/) by `.github/workflows/release.yml`, using **trusted publishing**: GitHub Actions proves its identity to PyPI with a short-lived OpenID Connect token, so no PyPI password or API token is stored in the repository or its secrets.

## One-time setup

Both settings must name the same repository, workflow file and environment.

**1. On PyPI** (an owner of the `pdl-taskmaster` project): open the project's **Manage → Publishing** page (`https://pypi.org/manage/project/pdl-taskmaster/settings/publishing/`) and add a GitHub trusted publisher:

| Field | Value |
|---|---|
| Owner | `paragon-ux` |
| Repository name | `PDLt-Test` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

**2. On GitHub** (a repository admin): **Settings → Environments → New environment**, named `pypi`. Recommended protections:

- **Required reviewers:** yourself, so each upload waits for your approval after the tests and build pass.
- **Deployment branches and tags:** "Selected branches and tags", with a tag rule `v*`.

No secrets are needed in the environment.

## Each release

1. **Version.** Set the same version in `VERSION` and `src/pdl_taskmaster/__init__.py` (`__version__`), following the existing scheme: a minor version for new features (2.5.1 to 2.6.0), a patch version for fixes only.
2. **Check locally**, from a source checkout with the test extras installed:

    ```bash
    python -m pytest -q -n auto
    python -m pytest tests/test_harness_anti_overfitting.py -W error
    python -m pip install build twine
    python -m build
    python -m twine check --strict dist/*
    ```

3. **Merge to `main`** with CI green.
4. **Create the release:** on GitHub, **Releases → Draft a new release**, tag `v<version>` (for example `v2.6.0`) on `main`, and publish it. Or: `gh release create v2.6.0 --target main --title "2.6.0" --generate-notes`.

Publishing the release starts `release.yml`:

| Job | What it does |
|---|---|
| `tests` | The full CI workflow (`ci.yml`): the offline suite and integrity gate on Linux and Windows, Python 3.10 to 3.14, and the distribution build on each interpreter |
| `build` | Checks the tag is `v` + `VERSION` + `__version__`, builds the sdist and wheel once, runs `twine check --strict`, installs the wheel outside the repository and runs `pdlt version`, an empty headless session and the sandbox check, then uploads `dist/` as an artifact |
| `publish` | In the `pypi` environment (and after your approval, if you set required reviewers), uploads exactly the built artifact to PyPI with `pypa/gh-action-pypi-publish`, which also attaches signed provenance attestations |

Only `publish` can request an identity token (`id-token: write`); every other job has read-only repository access.

## If something fails

| Symptom | Fix |
|---|---|
| `build` fails at "The tag matches the package version" | The tag and the version files disagree. Delete the release and its tag, fix the version, merge, and release again. |
| `publish` fails with `invalid-publisher` | The PyPI trusted publisher does not match: check owner, repository, workflow file name and environment name against the table above. |
| `publish` fails with "File already exists" | That version is already on PyPI; versions cannot be re-uploaded. Bump the version. |

## The documentation site

`.github/workflows/docs.yml` builds the site with Zensical and deploys it to GitHub Pages ([paragon-ux.github.io/PDLt-Test](https://paragon-ux.github.io/PDLt-Test/)) on every push to `main` that changes `docs/`, `zensical.toml` or `README.md`. Changes on other branches are not published until merged. Build it locally first with `zensical build`: it must report "No issues found".
