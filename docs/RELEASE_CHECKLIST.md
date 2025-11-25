# Release Checklist

Complete checklist for releasing a new version of Docling Hybrid OCR to PyPI.

---

## Pre-Release Preparation

### 1. Version Planning

- [ ] Determine version number following [Semantic Versioning](https://semver.org/)
  - MAJOR: Breaking API changes
  - MINOR: New features, backwards compatible
  - PATCH: Bug fixes, backwards compatible
- [ ] Create release milestone on GitHub
- [ ] Create release branch: `release/vX.Y.Z`

### 2. Code Quality

- [ ] All unit tests passing locally
  ```bash
  pytest tests/unit -v
  ```
- [ ] All integration tests passing (with OpenRouter API key)
  ```bash
  pytest tests/integration -v
  ```
- [ ] End-to-end tests passing
  ```bash
  pytest tests/e2e -v
  ```
- [ ] Linting passes with no errors
  ```bash
  ruff check src/
  ```
- [ ] Type checking passes
  ```bash
  mypy src/docling_hybrid
  ```
- [ ] Code coverage meets minimum threshold (>85%)
  ```bash
  pytest tests/ --cov=src/docling_hybrid --cov-report=term
  ```

### 3. Documentation Review

- [ ] Update `CHANGELOG.md` with all changes since last release
  - Added features
  - Changed APIs
  - Deprecated features
  - Removed features
  - Bug fixes
  - Security updates
- [ ] Update version number in:
  - [ ] `pyproject.toml`
  - [ ] `src/docling_hybrid/__init__.py`
  - [ ] `CHANGELOG.md` (unreleased → version)
- [ ] Review and update `README.md`
  - Current features accurate
  - Installation instructions tested
  - Examples work
  - Badges updated (if applicable)
- [ ] Review and update `docs/QUICK_START.md`
  - All examples tested
  - Screenshots/output current
  - Links working
- [ ] Review and update `docs/API_REFERENCE.md`
  - All public APIs documented
  - Examples working
  - Signatures accurate
- [ ] Review `docs/DEPLOYMENT.md`
  - Deployment steps tested
  - Docker instructions working
  - Environment variables documented

### 4. Dependency Check

- [ ] Review `pyproject.toml` dependencies
  - All dependencies still needed
  - Version constraints appropriate
  - No security vulnerabilities
    ```bash
    pip list --outdated
    ```
- [ ] Test with minimum supported Python version (3.11)
- [ ] Test with latest Python version (3.12)

### 5. Configuration Review

- [ ] Verify `.env.example` is current
- [ ] Verify `configs/default.toml` has production-ready defaults
- [ ] Verify `configs/local.toml` works for development
- [ ] Check `MANIFEST.in` includes all necessary files

---

## Build and Test

### 6. Local Build Test

- [ ] Clean previous builds
  ```bash
  rm -rf dist/ build/ *.egg-info
  ```
- [ ] Build source distribution
  ```bash
  python -m build --sdist
  ```
- [ ] Build wheel distribution
  ```bash
  python -m build --wheel
  ```
- [ ] Verify build artifacts in `dist/`
  ```bash
  ls -lh dist/
  ```
- [ ] Check package metadata
  ```bash
  python -m twine check dist/*
  ```

### 7. Test Installation

- [ ] Create fresh virtual environment
  ```bash
  python -m venv test-env
  source test-env/bin/activate
  ```
- [ ] Install from wheel
  ```bash
  pip install dist/docling_hybrid_ocr-X.Y.Z-py3-none-any.whl
  ```
- [ ] Verify CLI works
  ```bash
  docling-hybrid-ocr --version
  docling-hybrid-ocr backends
  ```
- [ ] Test basic conversion
  ```bash
  docling-hybrid-ocr convert tests/fixtures/sample.pdf
  ```
- [ ] Deactivate and remove test environment
  ```bash
  deactivate
  rm -rf test-env
  ```

### 8. Test PyPI Upload (Optional)

- [ ] Upload to TestPyPI
  ```bash
  python -m twine upload --repository testpypi dist/*
  ```
- [ ] Install from TestPyPI
  ```bash
  pip install --index-url https://test.pypi.org/simple/ docling-hybrid-ocr
  ```
- [ ] Verify installation and basic functionality
- [ ] Check package page: https://test.pypi.org/project/docling-hybrid-ocr/

---

## Release Execution

### 9. Git Release Preparation

- [ ] Ensure all changes committed
  ```bash
  git status
  ```
- [ ] Update version in all files (see checklist item 3)
- [ ] Commit version bump
  ```bash
  git add .
  git commit -m "chore: Bump version to vX.Y.Z"
  ```
- [ ] Create and push release tag
  ```bash
  git tag -a vX.Y.Z -m "Release vX.Y.Z"
  git push origin vX.Y.Z
  ```
- [ ] Push release branch
  ```bash
  git push origin release/vX.Y.Z
  ```

### 10. GitHub Release

- [ ] Go to GitHub Releases: https://github.com/docling-hybrid/docling-hybrid-ocr/releases
- [ ] Click "Draft a new release"
- [ ] Select the tag: `vX.Y.Z`
- [ ] Release title: `vX.Y.Z - [Release Name]`
- [ ] Copy relevant section from `CHANGELOG.md` into description
- [ ] Attach build artifacts (optional)
  - Source tarball: `dist/docling-hybrid-ocr-X.Y.Z.tar.gz`
  - Wheel: `dist/docling_hybrid_ocr-X.Y.Z-py3-none-any.whl`
- [ ] Check "This is a pre-release" if applicable (alpha, beta, RC)
- [ ] Click "Publish release"

### 11. PyPI Upload

- [ ] Ensure you have PyPI credentials configured
  ```bash
  # Check ~/.pypirc or use API token
  ```
- [ ] Upload to PyPI
  ```bash
  python -m twine upload dist/*
  ```
- [ ] Enter credentials when prompted (or use `--username __token__` with API token)
- [ ] Verify upload successful
- [ ] Check package page: https://pypi.org/project/docling-hybrid-ocr/

---

## Post-Release Verification

### 12. Installation Verification

- [ ] Wait 5-10 minutes for PyPI to process
- [ ] Create fresh virtual environment
  ```bash
  python -m venv verify-env
  source verify-env/bin/activate
  ```
- [ ] Install from PyPI
  ```bash
  pip install docling-hybrid-ocr
  ```
- [ ] Verify version
  ```bash
  docling-hybrid-ocr --version
  # Should show: docling-hybrid-ocr version X.Y.Z
  ```
- [ ] Test basic functionality
  ```bash
  # Set API key
  export OPENROUTER_API_KEY=your-key

  # Test conversion
  docling-hybrid-ocr convert sample.pdf
  ```
- [ ] Clean up
  ```bash
  deactivate
  rm -rf verify-env
  ```

### 13. Documentation Updates

- [ ] Verify PyPI package page displays correctly
  - README renders properly
  - Links working
  - Metadata accurate
- [ ] Update project homepage (if separate from GitHub)
- [ ] Update documentation site (if applicable)
- [ ] Post announcement on:
  - [ ] GitHub Discussions
  - [ ] Project blog (if applicable)
  - [ ] Social media (if applicable)
  - [ ] Relevant communities (Reddit, Discord, etc.)

### 14. Branch Management

- [ ] Merge release branch to `main`
  ```bash
  git checkout main
  git merge --no-ff release/vX.Y.Z
  git push origin main
  ```
- [ ] Merge `main` to `develop` (if using git-flow)
  ```bash
  git checkout develop
  git merge --no-ff main
  git push origin develop
  ```
- [ ] Delete release branch (optional)
  ```bash
  git branch -d release/vX.Y.Z
  git push origin --delete release/vX.Y.Z
  ```

---

## Monitoring

### 15. Post-Release Monitoring

- [ ] Monitor GitHub Issues for bug reports
- [ ] Monitor PyPI download stats
- [ ] Check CI/CD status for downstream builds
- [ ] Monitor community feedback (GitHub Discussions, social media)
- [ ] Document any immediate issues in tracking system

---

## Rollback Plan (If Needed)

If critical issues are discovered immediately after release:

### Option 1: Hotfix Release

- [ ] Create hotfix branch from tag
  ```bash
  git checkout -b hotfix/vX.Y.Z+1 vX.Y.Z
  ```
- [ ] Apply fixes
- [ ] Increment patch version
- [ ] Follow release process for hotfix version
- [ ] Yank problematic version from PyPI (use with caution)
  ```bash
  # This hides the version from new installs but doesn't delete it
  pip install twine
  twine yank docling-hybrid-ocr -v X.Y.Z
  ```

### Option 2: Yank Release

- [ ] Use `twine` to yank the release
  ```bash
  twine yank docling-hybrid-ocr -v X.Y.Z
  ```
- [ ] Post announcement about the issue
- [ ] Prepare corrected version ASAP

---

## Tools Required

Ensure these tools are installed before starting:

```bash
# Build tools
pip install build twine

# Development tools
pip install pytest pytest-cov ruff mypy

# Verify installation
python -m build --version
python -m twine --version
pytest --version
ruff --version
mypy --version
```

---

## Release Frequency

**Recommended Schedule:**
- **Patch releases:** As needed for critical bugs (within 24-48 hours)
- **Minor releases:** Every 2-4 weeks for new features
- **Major releases:** Every 3-6 months for breaking changes

**Version Lifecycle:**
- **Alpha (0.x.x):** Current status, breaking changes allowed
- **Beta (0.9.x):** Feature complete, API stabilizing
- **Stable (1.0.0+):** Semantic versioning, backwards compatibility

---

## Emergency Contact

For release-blocking issues:

1. Check GitHub Actions CI status
2. Review test failure logs
3. Contact tech lead if unable to resolve
4. Document issue in release notes
5. Consider delaying release if critical

---

## Notes

- **Never release on Friday** - Allows time for monitoring and quick fixes
- **Always test on clean environment** - Catches missing dependencies
- **Document breaking changes prominently** - Helps users upgrade smoothly
- **Keep CHANGELOG up to date** - Makes releases easier
- **Automate where possible** - Reduces human error

---

## Appendix: Version Numbering Examples

**Current:** 0.1.0 (Alpha)

**Next Versions:**
- **0.1.1** - Bug fix (e.g., fix retry logic bug)
- **0.2.0** - New feature (e.g., DeepSeek backend)
- **0.3.0** - New feature (e.g., progress callbacks)
- **1.0.0** - Stable release (API frozen, production ready)

**Breaking Changes:**
- If in alpha (0.x.x), increment minor: 0.1.0 → 0.2.0
- If stable (1.x.x+), increment major: 1.5.0 → 2.0.0

---

*Last Updated: 2025-11-25*
*Template Version: 1.0*
*For: Docling Hybrid OCR v0.1.0+*
