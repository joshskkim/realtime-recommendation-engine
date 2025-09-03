# GitHub Actions Workflow Configuration

## Workflow Structure

### Always Run
- **main.yml** - Core CI pipeline, runs on every PR and push

### Conditional Workflows
- **k8s-test.yml** - Runs when K8s configs or Dockerfiles change
- **code-quality.yml** - Runs when source code changes
- **security.yml** - Runs weekly and when dependencies change
- **performance.yml** - Runs daily and when perf tests change
- **docs.yml** - Runs when documentation changes
- **release.yml** - Runs on main branch pushes only

## Key Fixes Applied

### Kind Cluster Issue
Fixed by creating a temporary config file before cluster creation:
```yaml
- name: Create Kind config file
  run: |
    cat <<EOF > /tmp/kind-config.yaml
    kind: Cluster
    apiVersion: kind.x-k8s.io/v1alpha4
    nodes:
      - role: control-plane
      - role: worker
    EOF
```

### Workflow Optimization
- Split into focused workflows to reduce unnecessary runs
- Added path filters to trigger only relevant workflows
- Conditional execution based on file changes
- Scheduled runs for security and performance tests

## Usage
Place all workflow files in `.github/workflows/` directory