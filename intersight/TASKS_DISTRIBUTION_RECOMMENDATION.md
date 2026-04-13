# Recommendation: Distributing Ansible Task Files

## Question
How can users pull shared task files from GitHub similarly to how Ansible collections are downloaded?

## Short answer
Ansible does not natively load task files directly from a remote GitHub URL in `include_tasks` or `import_tasks`.

Task files must exist locally at runtime.

## Recommended approaches

1. Package shared task files in an Ansible role and install the role from GitHub using `ansible-galaxy`.
2. Package shared task files in an Ansible collection and install that collection from GitHub.
3. Use a repo bootstrap step (or git submodule/subtree) to clone/sync a tasks repository into a known local path before playbook execution.

## Best practice recommendation
Prefer a role or collection with pinned versions/tags.

Why:
- Reproducible runs
- Clear version control
- Better upgrade and rollback behavior
- Aligns with existing dependency workflows (`ansible-galaxy`)

## Example (role from GitHub)

`requirements.yml`

```yaml
---
roles:
  - name: intersight_shared_tasks
    src: https://github.com/your-org/intersight-shared-tasks.git
    scm: git
    version: v1.2.3
```

Install:

```bash
ansible-galaxy role install -r requirements.yml -p roles
```

Use from playbook:

```yaml
- name: Run shared profile lookup tasks
  ansible.builtin.include_role:
    name: intersight_shared_tasks
    tasks_from: profiles_lookups
```

## What to avoid
- Downloading raw task files from GitHub at playbook runtime
- Tracking floating `main`/`master` for shared task dependencies
- Copy-pasting task files across repositories (drift risk)

## Suggested next step for this repo
If desired, create a small `bootstrap-ansible.sh` that installs required collections and roles (with pinned versions) before running playbooks.
