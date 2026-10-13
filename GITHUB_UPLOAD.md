# Upload IslamicGuard to GitHub

This directory is a standalone Git repository on branch `main`. Its `origin`
remote points to `https://github.com/tsgunawan/IslamicGuard.git`.

## First upload

1. Sign in to GitHub as `tsgunawan` and create a **public** repository named
   `IslamicGuard`. Leave README, license and .gitignore initialization unchecked;
   those files are already present here.
2. Use this repository description:

   > IslamicGuard is a scholar-audited research framework for Islamic question answering with large language models. It includes layered guardrails, an English–Arabic benchmark, model outputs, scholar ratings, and reproducible analyses of citation accuracy, hallucinations, retrieval, and abstention.

3. In a terminal, run:

   ```bash
   cd /mnt/d/teddy/code/IslamicGuard/dist/islamicguard-release
   git status
   git remote -v
   git push -u origin main
   ```

   Authenticate using GitHub CLI (`gh auth login`) or a Git credential manager.
   GitHub account passwords cannot authenticate an HTTPS Git push. Keep tokens
   out of commands, repository files and remote URLs.

If a repository already exists and the push is rejected because it contains
commits, inspect its contents and history before deciding how to reconcile them.
Do not force-push over existing work.

## Licenses included

- `LICENSE`: standard MIT text for original software, prompts and documentation.
- `LICENSE-DATA.md`: CC BY 4.0 grant for original research data.
- `DATA_LICENSES.md` and `THIRD_PARTY_NOTICES.md`: exclusions and source attribution.
- `LICENSES/`: full license texts and supplied source notices.

Third-party benchmark items retain their source licenses. HalluTruthQA excerpts
remain CC BY-NC-ND 4.0, so the complete mixed benchmark is not unrestricted for
commercial reuse.

## Versioned release and DOI

After the first push, optionally enable this repository in Zenodo's GitHub
integration before publishing a GitHub release. Create a GitHub release with a
new tag `v1.0.0` targeting `main`. Describe the code, benchmark, run records,
scholar ratings and revision-2 analyses included.

After the release is published, update `CITATION.cff` with `version: 1.0.0`, the
actual `date-released` and the Zenodo DOI if one was minted; then commit and push.
The existing citation URL already points to this repository.

## Later updates

```bash
git add <changed-files>
git commit -m "Describe the change"
git push
```

Make public-release edits in this directory. The parent repository is the research
workspace; running its `scripts/make_release.py` overwrites this directory's files
and can restore internal references or omit these release-specific additions.

Official instructions: https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github
