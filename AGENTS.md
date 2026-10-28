# Agent guidance

## Albert Python plugin specification

- The authoritative specification is the upstream Albert Python provider's
  [`albert.pyi`](https://github.com/albertlauncher/albert-plugin-python/blob/main/albert.pyi).
  It documents metadata, API signatures and interface-version changes.
- Raw specification: https://raw.githubusercontent.com/albertlauncher/albert-plugin-python/main/albert.pyi
- This plugin targets Python interface **5.0** (`md_iid` in `__init__.py`).
  Before future migrations, check the upstream specification and confirm the
  target Albert Python provider supports the intended interface version.

## Validation

- Run offline regression tests with `python3 -B -m unittest discover -s tests -v`.
- The tests use Albert and dependency test doubles. They do not replace live
  validation inside Albert with the target Python provider, system keyring and
  GitHub API.