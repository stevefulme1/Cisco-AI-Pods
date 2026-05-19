# Changelog

All notable changes to **cisco.ai_pods** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-05-18

### Fixed

- Make TLS certificate verification configurable via `verify_ssl` parameter,
  defaulting to `True` (previously hardcoded `verify=False`)
- Remove global `urllib3.disable_warnings()` calls that suppressed TLS warnings

## [0.1.0] - 2026-05-15

### Added

- Ansible collection for deploying and managing Cisco AI Pod infrastructure
- Roles for Cisco Intersight server provisioning, OpenShift cluster setup, Pure Storage configuration, Portworx CSI deployment, and Splunk Observability integration
- Role README.md files for Galaxy import compliance

### Fixed

- Sanity ignore files for Helm templates and upstream shell scripts
- Correct sanity test names in ignore files (yamllint, syntax-check)
- Remove unskippable `load-failure` from ansible-lint skip_list
- Skip `yaml[document-start]` and `var-naming[no-role-prefix]` in ansible-lint
- Move `kubernetes.core` from `galaxy.yml` deps to requirements only
- Skip Python < 3.12 in sanity tests, fix ansible-lint offline mode
- Remove executable bit and non-module shebang from `generate_server_and_nmstate_templates.py`
- Certification workflow failures resolved
- Sanity ignore entries scoped to correct ansible-core versions (2.16 vs 2.17+)
