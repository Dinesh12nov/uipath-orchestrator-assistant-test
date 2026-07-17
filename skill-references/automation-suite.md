# Automation Suite — Install & Upgrade Guide (Kubernetes / OpenShift)

## Scope

Installation and upgrade of UiPath Automation Suite on an **existing/self-managed Kubernetes cluster**
(AKS, EKS) or Red Hat OpenShift — the "bring your own Kubernetes" deployment model, installed via the
`uipathctl` CLI and an `input.json` configuration file.

> **Important distinction — don't confuse this with "Automation Suite on Linux".**
> UiPath also ships a separate, self-managed-RKE2 install path ("Automation Suite on Linux",
> bare metal/VM) that provisions its own Kubernetes cluster and uses a *different* config file
> (`cluster_config.json`) and installer script (`install-uipath.sh`). That is a different guide
> and a different toolchain from the one below — if you're standing up RKE2 yourself rather than
> pointing the installer at an existing AKS/EKS/OpenShift cluster, use that guide instead.
> 📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide/automation-suite-overview
>
> **On GKE:** UiPath does not publish a dedicated "existing GKE cluster" install guide analogous to
> the EKS/AKS guide. GCP is supported through the self-managed "Automation Suite on Linux" installer
> running on GCP VMs (see the GCP deployment architecture doc), not as a bring-your-own-Kubernetes
> target. Treat "GKE" as unverified/unsupported for the workflow described in this file unless your
> UiPath account team confirms otherwise for your version.
> 📖 https://docs.uipath.com/automation-suite/automation-suite/2023.10/installation-guide/gcp-deployment-architecture

---

## Deployment Profiles

The `input.json` file has a single `"profile"` field. The only value confirmed in current UiPath
sample configurations is:

| Profile value | Use Case |
|---|---|
| `ha` | Production, high-availability multi-node deployment (the standard profile shown in UiPath's own AKS/EKS `input.json` examples) |

📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/aks-inputjson-example

> **Correction:** earlier drafts of this doc listed `single_node_serverless`, `multi_node_serverless`,
> `ha_prod`, and `custom` as selectable profile values. Those names could not be verified against
> current UiPath documentation for the AKS/EKS/OpenShift install path and appear to conflate this
> guide with the separate single-node-evaluation / multi-node-HA-ready-production terminology used
> for "Automation Suite on Linux". If you need a non-production/evaluation footprint on an existing
> Kubernetes cluster, confirm the exact supported configuration with current docs or your UiPath
> account team rather than relying on the profile names above.

> **Never use a non-HA/single-node footprint in production.** Data loss risk on node failure applies
> regardless of deployment model.

---

## Pre-Install Checklist (Kubernetes)

### Infrastructure Requirements

- [ ] Kubernetes version: Automation Suite supports a **rolling window of upstream N-1 to N-3**
  Kubernetes versions per Automation Suite Cumulative Update (CU) — there is no single fixed range.
  For example, AS 2023.10.12 supports K8s 1.31–1.33, while AS 2023.10.3 supported 1.27–1.29.
  Always check the compatibility matrix for your specific AS version/CU before provisioning nodes.
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/compatibility-matrix
- [ ] Node OS: varies by provider/version — e.g. Ubuntu 22.04 is the documented baseline for AKS;
  EKS documents specific RHEL/Amazon Linux/Bottlerocket combinations per EKS version (e.g. RHEL 8.8
  is called out specifically for EKS 1.33). Confirm against the compatibility matrix for your target
  version rather than assuming a fixed OS/version pair.
  📖 https://docs.uipath.com/automation-suite/automation-suite/2023.10/installation-guide-eks-aks/compatibility-matrix
- [ ] Node hardware — documented **minimum** to run the mandatory platform services (Identity,
  licensing, routing) plus Orchestrator is **8 vCPU / 16 GB RAM per node**. Larger, fewer nodes are
  more efficient than many small nodes (fixed per-node overhead). Use UiPath's Automation Suite
  Sizing/Capacity Calculator for your actual product mix and load rather than a flat number.
  Task Mining, if enabled, requires an additional dedicated node with 20 vCPU / 60 GB RAM.
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/kubernetes-cluster-and-nodes
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/capacity-planning

  > **Correction:** earlier drafts stated "16 vCPU / 32 GB RAM (production)" for server nodes — this
  > is roughly double the documented minimum. Don't over-provision blindly off this doc; size with
  > the calculator.
- [ ] Storage: Block storage CSI driver installed, with a default StorageClass set
- [ ] LoadBalancer or Ingress controller available (NGINX is the ingress controller UiPath documents
  configuring)
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/configuring-nginx-ingress-controller
- [ ] DNS entry pointing to cluster LoadBalancer IP/FQDN
- [ ] SSL certificate for cluster FQDN
- [ ] Outbound internet access (or air-gap with an OCI-compliant private registry configured)
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/configuring-the-oci-compliant-registry

### Tools Required on Install Machine

```bash
# Verify these are available
kubectl version --client
jq --version
openssl version

# Download the UiPath CLI used for install/upgrade (uipathctl) and versions.json
# for your target Automation Suite version — see "Downloading the installation packages"
```
📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/downloading-the-installation-packages
📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/running-uipathctl

### Pre-Install Network Checks

```bash
# Verify DNS resolves to cluster
nslookup <your-AS-fqdn>

# Test kubectl connectivity
kubectl get nodes
kubectl get namespaces
```

---

## Step-by-Step Install Checklist

### Phase 1 — Prepare input.json

- [ ] **1.1** Download the installation packages (`uipathctl`, `versions.json`) for your target
  Automation Suite version
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/downloading-the-installation-packages
- [ ] **1.2** Configure `input.json` — either by hand or using the Automation Suite Installer Wizard
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/configuring-inputjson
- [ ] **1.3** A trimmed example based on UiPath's published AKS reference (fields you'll actually
  need to touch for a typical HA install — see the source link for the full field list including
  per-product `external_object_storage` blocks, proxy, snapshot/backup, etc.):

```json
{
  "kubernetes_distribution": "aks",
  "install_type": "online",
  "profile": "ha",
  "registries": {
    "docker": {
      "url": "registry.uipath.com",
      "username": "<your-uipath-portal-email>",
      "password": "<your-uipath-portal-password>"
    },
    "helm": {
      "url": "registry.uipath.com",
      "username": "<your-uipath-portal-email>",
      "password": "<your-uipath-portal-password>"
    }
  },
  "fqdn": "automationsuite.company.com",
  "admin_username": "admin",
  "admin_password": "<strong-password>",
  "sql": {
    "create_db": false,
    "server_url": "<sql-host>",
    "port": "1433",
    "username": "<sql-user>",
    "password": "<sql-pass>"
  },
  "orchestrator": { "enabled": true },
  "storage_class": "<your-default-storageclass>"
}
```
📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/aks-inputjson-example (full sample, AKS)
📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/eks-inputjson-example (full sample, EKS)

  > **Correction:** earlier drafts of this doc used `cluster_config.json` with fields like
  > `multiNode`, `rke_token`, `fixed_rke_address`, and a nested `infra.docker_registry` block, plus
  > a top-level `smtp` block. Those fields belong to the separate "Automation Suite on Linux" (RKE2)
  > config schema, not the `input.json` used for AKS/EKS/OpenShift installs, and could not be
  > verified for this deployment path — they've been removed rather than guessed at. If you need
  > SMTP configuration for this install type, check the current `input.json` reference for your
  > version.

- [ ] **1.4** Validate JSON syntax: `jq . input.json`

### Phase 2 — Run the Installer (uipathctl)

```bash
# Check infrastructure prerequisites
./uipathctl prereq run input.json --versions versions.json

# Dry run first (simulates the apply, does not deploy)
./uipathctl manifest apply --dry-run input.json --versions versions.json

# Full install
./uipathctl manifest apply input.json --versions versions.json
```
📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/reference-guide/uipathctl-manifest-apply
📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/checking-the-infrastructure-prerequisites

> **Correction:** earlier drafts referenced a script named `installUiPathAS.sh` with `--dry-run`/
> plain invocation against `cluster_config.json`. That script name does not match current UiPath
> documentation for either install path (the RKE2/Linux path uses `install-uipath.sh`; the
> AKS/EKS/OpenShift path uses the `uipathctl` binary shown above).

- [ ] **2.1** Monitor install progress
- [ ] **2.2** Watch for pod failures during install:
  ```bash
  watch kubectl get pods -n uipath
  ```

### Phase 3 — Post-Install Validation

- [ ] **3.1** Verify all pods Running/Completed:
  ```bash
  kubectl get pods -n uipath | grep -v "Running\|Completed"
  # Should return no results if healthy
  ```

- [ ] **3.2** Verify ArgoCD applications are Synced:
  ```bash
  kubectl get applications -n argocd
  # All should show: SYNC STATUS = Synced, HEALTH STATUS = Healthy
  ```
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/managing-the-cluster-in-argocd

- [ ] **3.3** Run the built-in health check:
  ```bash
  ./uipathctl health check --namespace uipath --versions versions.json
  ```
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/upgrading-automation-suite

- [ ] **3.4** Access the unified Automation Suite portal at `https://<fqdn>` — there are no
  separate `/orchestrator_` or `/identity_` path prefixes like Standalone Orchestrator's IIS
  virtual directories; all products live behind one portal, and you switch **organization**
  inside it (an earlier draft's path-prefix claim didn't match the real access model and has
  been corrected):
  - Switch to the **Default** organization, username `orgadmin`, to reach org-level pages
    (Orchestrator, etc.)
  - Switch to the **Host** organization, username `admin`, for host-level administration
  - Retrieve either password with:
    ```bash
    kubectl get secret platform-service-secrets -n <uipath> -o jsonpath='{.data.identity\.hostAdminPassword}' | base64 -d ; echo
    ```
    (org admin and host admin share the same initial password by design)
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/accessing-automation-suite

- [ ] **3.5** Check the other management UIs are reachable:
  - ArgoCD: `https://alm.<fqdn>` — username `admin`, password via
    `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d`
  - Monitoring: `https://monitoring.<fqdn>/grafana`, `/metrics` (Prometheus), `/alertmanager`
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/accessing-automation-suite

- [ ] **3.6** Run resource health check:
  ```bash
  kubectl get pods -n uipath -o wide
  kubectl top nodes
  kubectl top pods -n uipath
  ```

---

## Upgrade Checklist (Automation Suite)

### Pre-Upgrade

- [ ] **Only relevant if your CURRENT version predates 2023.10: confirm no Classic folders/robots remain before upgrading to a 2023.10+ target.**
  If you're already on 2023.10 or later today (e.g. 2023.10 → 2024.10, or 2023.x → 2025.x), Classic
  folders cannot exist on your system — they'd have had to be migrated away already to reach your
  current version — so this doesn't apply. Only for a customer still on a pre-2023.10 version
  (2021.10/2022.4/2022.10/2023.4) targeting 2023.10+ for the first time: this blocks setup outright
  if any classic objects are still present. Migrate to Modern folders and delete classic folders
  first — see `references/classic-to-modern-folders.md`.
- [ ] **Check the compatibility matrix** for your current → target AS version hop (not all version
  hops are supported)
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/compatibility-matrix
- [ ] **Download `versions.json` and `uipathctl`** for the version you're upgrading to
- [ ] **Generate the latest `input.json`** (don't hand-edit a stale copy):
  ```bash
  ./uipathctl manifest get-revision
  # or, to see all past revisions:
  ./uipathctl manifest list-revisions
  ```
- [ ] **Back up the cluster and SQL/PostgreSQL database.** For AKS/EKS this means your configured
  cluster backup solution (Velero-based, or — from AS 2025.10 onward — your cloud provider's native
  AKS/EKS backup service) plus a SQL Server/PostgreSQL backup, **not** an etcd snapshot script (that
  applies to the separate self-managed-RKE2 install path).
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/backing-up-and-restoring-the-cluster
  📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/upgrading-automation-suite

  > **Correction:** earlier drafts specified `./configureUiPathAS.sh etcd-snapshot` and "backup
  > cluster_config.json" — both belong to the self-managed RKE2 path, not AKS/EKS/OpenShift.
- [ ] **Confirm ArgoCD is healthy** — no stuck syncs:
  ```bash
  kubectl get applications -n argocd
  ```
- [ ] **Check node capacity** — upgrade requires headroom for rolling restarts

### Upgrade Execution

```bash
# 1. Confirm the cluster is healthy before starting
./uipathctl health check --namespace uipath --versions versions.json

# 2. Put the cluster into maintenance mode (this causes downtime)
./uipathctl cluster maintenance enable
./uipathctl cluster maintenance is-enabled

# 3. Take your backup here (cluster + SQL), then disable maintenance mode
#    (maintenance mode must be OFF before the upgrade itself runs)
./uipathctl cluster maintenance disable

# 4. Run the upgrade
./uipathctl cluster upgrade input.json --versions versions.json

# 5. Confirm health after upgrade
./uipathctl health check --namespace uipath --versions versions.json
```
📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/upgrading-automation-suite

> **Correction:** earlier drafts used `./installUiPathAS.sh cluster_config.json --upgrade`. There is
> no evidence of an installer script by that name or a bare `--upgrade` flag in current UiPath
> documentation for this deployment path; the real command is `uipathctl cluster upgrade input.json
> --versions versions.json`, wrapped in the maintenance-mode sequence above.
>
> Separately, upgrading the underlying Kubernetes infrastructure itself (AKS/EKS version) is **your**
> responsibility, not something the Automation Suite installer does — follow your cloud provider's
> standard cluster-upgrade process, respecting the N-1..N-3 compatibility window.

### Post-Upgrade Validation

- [ ] All ArgoCD apps: `Synced` + `Healthy`
- [ ] All pods: `Running` or `Completed`
- [ ] `./uipathctl health check --namespace uipath --versions versions.json` passes
- [ ] Orchestrator portal accessible and version updated
- [ ] Test Robot connection and job execution
- [ ] Check for OOMKilled pods (memory pressure after upgrade):
  ```bash
  kubectl get pods -n uipath | grep OOMKill
  kubectl describe pod <pod-name> -n uipath | grep -A5 "OOMKilled"
  ```

---

## Common AS Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| Pod `OOMKilled` | Memory limit too low | Increase memory requests/limits via your input.json/resource-override configuration and re-apply. This is standard Kubernetes remediation; UiPath doesn't publish per-pod memory tuning tables, so confirm the right override mechanism for the affected component before changing values. |
| ArgoCD sync loop | Self-heal fighting a manual patch | Disable self-heal on the affected ArgoCD Application before patching; re-enable after. Standard ArgoCD administration — see UiPath's cluster/ArgoCD management doc. 📖 https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/managing-the-cluster-in-argocd |
| `redisenterpriseclusters not found` / Redis probe failure | Redis Enterprise cluster lost contact with more than half its nodes, or CRDs/finalizers are stuck | This is a documented UiPath procedure — see **Redis Cluster Recovery** below rather than improvising finalizer removal. 📖 https://docs.uipath.com/automation-suite/automation-suite/2023.10/installation-guide/redis-probe-failure |
| `MetadataAddress must use HTTPS` | Identity/OIDC metadata endpoint being called over HTTP instead of HTTPS | **Unverified for Automation Suite specifically** — this error is documented for standalone Orchestrator/Identity Server (ASP.NET Core OIDC `RequireHttpsMetadata`), but the specific internal cluster URL and "wrong path prefix" root cause claimed in an earlier draft could not be confirmed against Automation Suite docs. Don't apply the internal URL fix from the earlier draft as-is — check the current Identity Server troubleshooting doc for your AS version and confirm FQDN/redirect URI configuration is HTTPS end-to-end. 📖 https://docs.uipath.com/orchestrator/standalone/2023.4/installation-guide/identity-server-troubleshooting |
| Persistent Volume stuck `Pending` | StorageClass not set as default | `kubectl patch storageclass <name> -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'` — standard Kubernetes administration, not AS-specific |
| Image pull `ErrImagePull` | Registry credentials expired/incorrect | Update credentials under `registries.docker` / `registries.helm` in `input.json` and re-apply (`uipathctl manifest apply input.json --versions versions.json`) |

## Redis Cluster Recovery (Documented Procedure — Redis Probe Failure)

This is UiPath's own documented recovery procedure for Redis probe failures, not a customer-specific
runbook — an earlier draft of this doc labeled it "BofA Pattern," which is unverifiable/unjustified
customer attribution and has been removed. Source:
📖 https://docs.uipath.com/automation-suite/automation-suite/2023.10/installation-guide/redis-probe-failure

**Description:** the Redis probe can fail if the node ID file doesn't exist (pod not yet
bootstrapped). There is also an automatic recovery job — do **not** run the manual steps below while
that job is already running. This same manual procedure applies when a Redis Enterprise cluster
loses contact with more than half its nodes (node failure or network split) and pods fail to rejoin.

```bash
# 1. Disable ArgoCD self-heal on all three related applications
kubectl -n argocd patch application fabric-installer --type=json \
  -p '[{"op":"replace","path":"/spec/syncPolicy/automated/selfHeal","value":false}]'
kubectl -n argocd patch application redis-cluster --type=json \
  -p '[{"op":"replace","path":"/spec/syncPolicy/automated/selfHeal","value":false}]'
kubectl -n argocd patch application redis-operator --type=json \
  -p '[{"op":"replace","path":"/spec/syncPolicy/automated/selfHeal","value":false}]'

# 2. Delete the Redis database and cluster resources, then remove their finalizers
kubectl delete redb -n redis-system redis-cluster-db --force --grace-period=0 &
kubectl delete rec -n redis-system redis-cluster --force --grace-period=0 &
kubectl patch redb -n redis-system redis-cluster-db --type=json \
  -p '[{"op":"remove","path":"/metadata/finalizers","value":"finalizer.redisenterprisedatabases.app.redislabs.com"}]'
kubectl patch rec redis-cluster -n redis-system --type=json \
  -p '[{"op":"remove","path":"/metadata/finalizers","value":"redbfinalizer.redisenterpriseclusters.app.redislabs.com"}]'

# 3. Force-delete the services-rigger pod and the redis-cluster-0/1/2 pods
kubectl -n redis-system get pods | grep services-rigger | awk '{print $1}' | xargs kubectl -n redis-system delete pod --force
kubectl -n redis-system get pods | grep -E "redis-cluster-[0-2]" | awk '{print $1}' | xargs kubectl -n redis-system delete pod --force

# 4. Re-enable ArgoCD self-heal
kubectl -n argocd patch application fabric-installer --type=json \
  -p '[{"op":"replace","path":"/spec/syncPolicy/automated/selfHeal","value":true}]'
kubectl -n argocd patch application redis-cluster --type=json \
  -p '[{"op":"replace","path":"/spec/syncPolicy/automated/selfHeal","value":true}]'
kubectl -n argocd patch application redis-operator --type=json \
  -p '[{"op":"replace","path":"/spec/syncPolicy/automated/selfHeal","value":true}]'

# 5. Trigger the recovery job manually
kubectl -n redis-system create job --from=cronjob/redis-cluster-recovery-job cronjob-manual-run
```

If the issue persists after this, check for **clock skew** between Kubernetes nodes — Redis pods
fail to run on a node whose clock is even a few seconds off. Sync all node clocks (NTP/chrony) and
retry.

> **Correction:** the earlier draft's version of this procedure only patched the `redis-cluster`
> ArgoCD application (omitting `fabric-installer` and `redis-operator`), omitted the pod
> force-deletion step for `services-rigger` and `redis-cluster-0/1/2`, and used a different manual
> job name (`manual-recovery` instead of the documented `cronjob-manual-run`). Those omissions can
> leave the recovery incomplete — the sequence above matches UiPath's published steps exactly.

---

## Reference Links

> UiPath's Automation Suite docs are version-pinned in the URL (e.g. `.../automation-suite/2024.10/...`)
> — there is no `/automation-suite/latest/` path. Swap `2024.10` for your installed version/CU when
> following these links, and note EKS/AKS and OpenShift have separate guide trees
> (`installation-guide-eks-aks` vs `installation-guide-openshift`).

- AS on EKS/AKS install guide: https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/installing-automation-suite
- AS on OpenShift install guide: https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-openshift/installing-automation-suite
- AS on EKS/AKS upgrade guide: https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/upgrading-automation-suite
- Kubernetes cluster and node requirements: https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/kubernetes-cluster-and-nodes
- Compatibility matrix (K8s versions, third-party components): https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/compatibility-matrix
- Troubleshooting (EKS/AKS): https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/troubleshooting
- Redis probe failure (self-managed RKE2 guide, same procedure applies): https://docs.uipath.com/automation-suite/automation-suite/2023.10/installation-guide/redis-probe-failure
