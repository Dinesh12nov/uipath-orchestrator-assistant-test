# Standalone Orchestrator → Automation Cloud Migration Guide

## Scope
Migration from self-hosted Standalone Orchestrator to UiPath Automation Cloud (SaaS).
Covers data migration, Robot reconnection, license transfer, and cutover planning.

> **UiPath provides two official migration paths — use one of these first, not the checklist below, as your primary method:**
> 1. **Automation Cloud Migration Tool** (recommended) — a downloadable desktop app that connects to your Standalone Orchestrator and automatically exports/imports most entities (folders, machines, packages, libraries, calendars, queues, processes, robots, environment associations, triggers-as-disabled, most assets) into your cloud tenant. 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/using-the-migration-tool
> 2. **Manual migration** — UiPath's own documented step-by-step manual process for recreating a Standalone tenant in Cloud Orchestrator. 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/manual-migration
>
> Neither official path is fully automatic: the Migration Tool does **not** migrate user/robot accounts, role assignments, queue items, action catalogs, webhooks, testing entities, storage buckets, logs, tasks, machine keys, or personal workspace folders — and it does not perform cutover. A few entities migrate only **partially**: Settings (passwords/secret values always excluded, re-enter manually), Packages (feeds using external/custom authentication excluded), Libraries (tenant-level only, not folder-scoped), and Triggers (imported disabled, without per-robot configuration). **This checklist is meant as an internal supplement/fallback that fills those gaps and adds PSE-specific verification steps**, not a replacement for the official tooling. Overview: 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/about-migrating-to-automation-cloud

---

## Migration Decision Matrix

Before starting, answer these:

| Question | If YES | If NO |
|---|---|---|
| Is your on-prem Orchestrator on a supported version, on Windows, and do you have a **dedicated user account** (not a robot account) with admin rights and **View permission on every folder being migrated** — the tool's folder export silently fails for folders that account can't see — plus enough cloud robot licenses for all robots being migrated? | Use the **Automation Cloud Migration Tool** as your primary method (📖 [using-the-migration-tool](https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/using-the-migration-tool)) | Fall back to full **Manual Migration** (📖 [manual-migration](https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/manual-migration)) |
| Do you need to preserve historical job/queue data? | Plan data export — queue items, logs, and storage buckets are **not** migrated by either official path | Simple cutover possible |
| Do you have custom Orchestrator configurations? | Document all settings first | Standard migration |
| Are you still on **Classic Folders**? | Migrate to Modern Folders **before** migrating to cloud — Classic Folders are not supported in cloud platforms. 📖 https://docs.uipath.com/overview/other/latest/overview/classic-folders-removal | Proceed with migration |
| Do you use **Machine Templates with robot-account or unattended-user-account mappings**? | **Known failure mode** — pre-create/pre-provision each mapped account at the **tenant level** (Manage Access) in the destination Cloud org *before* running the Migration Tool. Existing only at the org level is not sufficient — this is the most common real-world migration failure, surfacing as the literal error `Some of the robots provided do not exist`. 📖 Internal reference: "UiPath Automation Cloud Migration Runbook" (DOC-26901 / PLT-100541) | No account-mapped machine templates — lower risk here |
| Are Robots on Windows VMs or VDI? | Standard Robot reconnection | May need cloud robot setup |
| Are you using Standalone Identity (SSO/AD)? | Plan SSO reconfiguration for cloud | Standard migration |
| Do you use credential stores (CyberArk/AKV)? | Read `cloud-onboarding.md` | Standard migration |
| Current version not supported per UiPath's Product Lifecycle? | Upgrade Standalone first, then migrate | Proceed with migration | 
| Current version older than **22.10**? | The Modern Folder migration wizard has only been available since Orchestrator 22.10 (not just 2023.10+) — upgrade to at least 22.10 first, migrate Classic folders to Modern, **then** proceed with the Cloud migration | Modern Folder migration is already available; proceed once Classic folders (if any) are resolved |
| Does your network currently restrict outbound traffic by firewall? | Confirm the required FQDN allowlist (`cloud.uipath.com:443`, `*.service.signalr.net:443`, plus region-specific relay/tunnel hosts) is in place **before** cutover — robots and users can't reach Automation Cloud otherwise. Also check whether your firewall rules are IP-based: UiPath is transitioning to unified outbound IP ranges, with a **September 16, 2026** deadline to add the new ranges alongside the legacy ones (don't remove legacy ranges until a later release note confirms it's safe). 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/configuring-the-firewall-for-cloud | Standard migration, but still confirm outbound HTTPS (443) isn't blocked by default |

---

## Migration Checklist

### Phase 1 — Pre-Migration Inventory (Source — Standalone)

Document everything from the existing Standalone Orchestrator. If you're using the Migration Tool, most of this is captured automatically during its export step — this list is primarily for the manual path or for verifying the tool's export summary:

- [ ] **1.1** Export Tenants list (names, user counts, folder structure)
- [ ] **1.2** Export/note all Packages (names, versions) from `Storage` folder or NuGet feed
- [ ] **1.3** Export Assets list (names, types, folder assignments) — DO NOT export values for credentials
- [ ] **1.4** Export Queues (names, SLA settings, folder assignments)
- [ ] **1.5** Export all Process/Schedule configurations
- [ ] **1.6** List all Machines and connected Robot machines (hostnames) — 📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/about-machines
- [ ] **1.7** List all Users and their roles — note that user/robot accounts and role assignments are **not** migrated by the Migration Tool and must be recreated
- [ ] **1.8** Note all Webhook configurations (not migrated by the Migration Tool — 📖 [entities not migrated](https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/using-the-migration-tool#entities-not-migrated-by-the-migration-tool))
- [ ] **1.9** Note current license counts (Unattended, Attended, Studio, etc.)
- [ ] **1.10** Screenshot all custom Settings (Orchestrator → Settings)
- [ ] **1.11** Note SMTP configuration (host, port, auth) — needed for cloud setup
- [ ] **1.12** Document any external integrations (Jira, ServiceNow, etc.)

### Phase 2 — Prepare Automation Cloud Tenant

- [ ] **2.0** If using the Migration Tool: temporarily disable any active organizational
  policies in Automation Cloud that could interfere with the import step (they can block
  entity creation mid-import) — re-enable them once migration is complete.
  📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/using-the-migration-tool
- [ ] **2.1** Provision Automation Cloud tenant at `https://cloud.uipath.com`
- [ ] **2.1a** If any Machine Template maps to a robot account or an unattended-user account,
  inventory every one of those mappings and pre-create/pre-provision each account at the
  **tenant level** (Manage Access) in this Cloud org before migrating machines — existing only
  at the org level is not sufficient. This is the single most common real-world migration
  failure; skipping it surfaces as `Some of the robots provided do not exist` during the
  machine/template migration step. 📖 Internal reference: "UiPath Automation Cloud Migration
  Runbook" (DOC-26901 / PLT-100541); real case illustration: "TLG - Cloud Migration"
- [ ] **2.2** Activate licenses — confirm seat counts match or exceed Standalone (see **License Transfer** below)
- [ ] **2.3** Configure SSO/Identity (Azure AD/Entra ID, SAML) if used
  - Navigate: Admin → Organization → Security → Authentication settings — 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/setting-up-saml-sso-with-azure-ad
- [ ] **2.4** Recreate Folder structure in cloud Orchestrator (or let the Migration Tool do this)
- [ ] **2.5** Invite users and assign roles (or sync via Azure AD/Entra ID groups) — not handled by the Migration Tool
- [ ] **2.6** Configure SMTP if email notifications required:
  - Admin → your org → **Mail Settings** page (live docs confirm this is the current label, not "System email notifications") — 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/configuring-system-email-notifications

### Phase 3 — Migrate Packages

If using the Migration Tool, packages and package versions are migrated automatically (with the exception of feeds requiring external authentication). For the manual path, packages can be uploaded via the Orchestrator UI or via the Orchestrator API:

```powershell
# Option A — Manual: Upload packages via Orchestrator UI
# Orchestrator → Packages → Upload (.nupkg files, 30 MB size limit by default)
# 📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-packages

# Option B — API bulk upload (PowerShell)
# Endpoint and multipart/form-data usage below are documented informally by UiPath/community
# (see Orchestrator API guide + Swagger definition for your tenant to confirm current behavior):
# 📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/api-guide/packages-requests
# Note: this endpoint has historically required that an OLDER version of the package
# already exists in the target Orchestrator — verify against your tenant's Swagger spec
# before relying on it for a first-time bulk upload.
$orchestratorUrl = "https://cloud.uipath.com/<org>/<tenant>/orchestrator_"
$headers = @{ "Authorization" = "Bearer <token>" }
$packages = Get-ChildItem "C:\Backup\Packages" -Filter "*.nupkg"
foreach ($pkg in $packages) {
    $form = @{ file = Get-Item $pkg.FullName }
    Invoke-RestMethod -Uri "$orchestratorUrl/odata/Processes/UiPath.Server.Configuration.OData.UploadPackage" `
        -Method POST -Headers $headers -Form $form
}
```

- [ ] **3.1** Upload all NuGet packages to cloud Orchestrator (or verify Migration Tool import summary)
- [ ] **3.2** Verify package versions match source
- [ ] **3.3** Recreate Process configurations linked to uploaded packages

### Phase 4 — Migrate Assets & Queues

> ⚠️ **Credential assets**: Never export credential values — recreate them manually in cloud. The Migration Tool migrates most asset types but does **not** migrate per-user asset values in modern folders.

- [ ] **4.1** Recreate all text/integer/boolean assets in cloud (Migration Tool handles this automatically, or use the Assets API for a manual bulk import) — 📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-assets-in-orchestrator
- [ ] **4.2** Recreate credential assets — enter values fresh (do not copy from source)
- [ ] **4.3** Recreate all Queues with same SLA settings
- [ ] **4.4** Recreate Schedules / Triggers — note triggers imported by the Migration Tool are created **disabled** and must be manually re-enabled

### Phase 5 — Reconnect Robots

Robots can only be connected to **one** Orchestrator at a time — connecting a Robot to the cloud tenant automatically disconnects it from the on-prem Orchestrator and consumes a new cloud license. 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/manual-migration#manually-recreating-your-orchestrator-setup — machine keys are **not** migrated by the Migration Tool, so this step is always manual regardless of which path you used.

For **each Robot machine**:

- [ ] **5.1** Ensure the machine is not running active jobs, then disconnect the Robot from the source Orchestrator via UiPath Assistant → Preferences → Orchestrator Settings, or via CLI (`UiRobot.exe disconnect`) — **no need to uninstall** the Robot
- [ ] **5.2** Connect the Assistant to the cloud tenant. Note: the live "Connecting Robots to
  Orchestrator" doc currently documents **Service URL** (interactive sign-in) and **Client ID**
  (client credentials) as the two Assistant connection types — "Machine Key" is no longer shown
  as a distinct selectable option in the Assistant UI, though the concept survives via Hybrid
  auth mode and the CLI `--key` flag below. Use whichever connection type matches your Robot's
  auth mode (Hybrid machines still use a machine key under the hood):
  - Orchestrator URL: `https://cloud.uipath.com/<org>/<tenant>/`
  - Machine Key (Hybrid/CLI path): copy from cloud Orchestrator → Tenant → Machines → [Machine object] → Machine Key
  - 📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/robot-authentication
- [ ] **5.3** In cloud Orchestrator, ensure the Machine object and Robot/user account are added to the target folder
- [ ] **5.4** Verify Robot shows as **Connected**/**Available** in cloud Orchestrator monitoring
- [ ] **5.5** Run a test process on the reconnected Robot

**Robot reconnection via CLI (on each Robot machine):**
```powershell
# Correct UiRobot.exe CLI syntax (verified against Robot CLI docs):
# 📖 https://docs.uipath.com/robot/standalone/latest/admin-guide/command-line-interface
$cloudUrl = "https://cloud.uipath.com/<org>/<tenant>/"
$machineKey = "<machine-key-from-cloud-orchestrator>"

# Note: exact install path varies by install mode
# (Service Mode: %ProgramFiles%\UiPath\...; User Mode: %LocalAppData%\Programs\UiPath\...)
# — confirm the path on your target machine before scripting this at scale.
& "C:\Program Files\UiPath\Robot\UiRobot.exe" connect --url $cloudUrl --key $machineKey

# To disconnect from the old Orchestrator first (optional — connecting to a new
# Orchestrator switches the connection automatically):
# UiRobot.exe disconnect --wait
```

### Phase 6 — Cutover

- [ ] **6.1** Choose cutover window (low-activity period)
- [ ] **6.2** Stop all schedules/triggers on Standalone Orchestrator
- [ ] **6.3** Wait for all active jobs to complete (or gracefully stop)
- [ ] **6.4** Enable schedules/triggers in cloud Orchestrator (remember: Migration Tool imports triggers as disabled)
- [ ] **6.5** Redirect users to cloud Orchestrator URL
- [ ] **6.6** Update any hardcoded Orchestrator URLs in Robot processes
- [ ] **6.7** Run full smoke test (trigger each critical process once)
- [ ] **6.8** Keep Standalone Orchestrator running in read-only mode for a defined rollback window (e.g., 2 weeks) as a project decision — this is general practice, not a UiPath-documented requirement

### Phase 7 — Post-Migration Validation

- [ ] All Robots connected and showing **Online** in cloud
- [ ] All Processes visible and executable
- [ ] All Assets retrievable (test via Robot process)
- [ ] Schedules running at expected times
- [ ] Email notifications working
- [ ] SSO login working for all users
- [ ] Historical data accessible (if migrated — note queue items, logs, and storage buckets are not migrated by either official path)
- [ ] License consumption within expected range
- [ ] If using the Migration Tool: manually complete its documented post-migration tasks (allocate licenses, upload library feeds, create skipped robots, recreate webhooks/task catalogs/credential stores, connect robots, enable triggers, re-enter passwords) — 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/using-the-migration-tool#post-migration-tasks

---

## License Transfer

Cloud licenses are **not** activated using a Standalone deactivation key. The real process:

```
1. Contact your UiPath Account Team / Support to request a cloud License Code
   sized to match your Standalone entitlement (named user vs. concurrent/unattended
   robot counts may need to be re-quoted if the license type changes).
   📖 https://customerportal.uipath.com/support/add-case
2. In Automation Cloud: Admin → Licenses → Enterprise Activation → paste the License Code → Activate.
   📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/activating-your-license
3. Allocate licenses to tenants and users as needed.
   📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/allocating-licenses-to-tenants
```

> **Note:** UiPath can issue a temporary license key that extends a trial period specifically to cover the migration window, so the same product license can effectively be used on both Standalone and Cloud while cutover is in progress — request this from Support/your Account Team rather than assuming a self-service deactivation/reactivation flow. 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/about-migrating-to-automation-cloud#setup-before-migration
>
> The Standalone Orchestrator **offline deactivation/activation** flow (Settings → License → Deactivate, producing a file uploaded at the Activation Portal) is a real UiPath feature, but it is designed for transferring a license between two on-prem/offline Orchestrator instances — not for provisioning Automation Cloud. 📖 https://docs.uipath.com/orchestrator/standalone/2023.10/user-guide/managing-your-host-license

---

## Rollback Plan

If migration fails during cutover:
1. Stop all cloud Orchestrator jobs
2. Re-enable IIS on Standalone Orchestrator server
3. Reconnect Robots to Standalone (restore original Machine Key) — remember Robots can only be connected to one Orchestrator at a time, so this will disconnect them from cloud
4. Resume operations on Standalone
5. Investigate and reattempt migration after fixing root cause

---

## Common Migration Errors

| Error | Cause | Fix |
|---|---|---|
| Robot shows `Disconnected` after reconnect | Machine not added to the target folder | Add the Machine object to the target folder in cloud — 📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/about-machines |
| `An unattended robot has not been configured` | Domain credentials not set for the robot account | Set `domain\username` + password on the Robot/Machine mapping in the target folder — 📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/robot-authentication |
| Asset not found errors in Robot | Asset not recreated in cloud | Recreate missing asset in cloud; verify folder assignment |
| Package not found | Upload failed or wrong folder | Re-upload package; check folder assignment |
| SSO login fails | Redirect URI mismatch | Update Reply URL in Azure AD/Entra ID app registration to include the cloud URL — 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/setting-up-saml-sso-with-azure-ad |
| `Some of the robots provided do not exist` during machine/template migration | A Machine Template's account mapping (robot account or unattended-user account) exists at the org level but was never pre-created at the **tenant level** (Manage Access) in the destination Cloud tenant | Pre-create/pre-provision the mapped account at the tenant level before re-running the migration step — see Phase 2.1a |

---

## Internal Case Patterns & Known Issues (Confluence-sourced)

Recurring patterns pulled from internal UiPath Confluence pages (Support Knowledge Base and Site
Reliability spaces), useful for sanity-checking a migration plan even when the customer's
situation looks "standard":

- **"Some of the robots provided do not exist"** — the most frequently recurring real failure,
  root-caused every time to a Machine Template account mapping that exists at the org level but
  was never pre-created at the tenant level. Seen in at least two distinct real cases with
  different mapping styles (robot account; local unattended-user account). *(Source: "UiPath
  Automation Cloud Migration Runbook", "TLG - Cloud Migration")*
- **Silent failures leaving stale status** — the migration tool can report a misleading
  "in progress" or partially-successful state rather than a clear failure; verify actual entity
  counts in the destination tenant rather than trusting the tool's own status indicator alone.
  *(Source: "Region Migration Case Studies")*
- **Org-before-tenant dependency** — org-level setup (policies, license provisioning, account
  pre-creation) repeatedly turns out to be the actual blocker on cases scoped as "just a tenant
  migration." Treat org-level readiness as a hard prerequisite gate, not a parallel task.
  *(Source: "Region Migration Case Studies")*
- **AI Center, IXP, Maestro, and Data Unit content, plus audit logs, are not portable** between
  environments/regions — plan these separately rather than assuming they migrate.
  *(Source: "Region Migration Case Studies")*
- **Scale-unit and plan-tier mismatches** between source and destination region/tenant have
  caused real project delays when not checked up front. *(Source: "Region Migration Case
  Studies")*
- **Realistic project timelines** for non-trivial cloud migrations in documented cases ranged
  from about 15 to 70+ days — set customer expectations accordingly rather than promising a
  single-weekend cutover. *(Source: "Region Migration Case Studies")*

---

## Reference Links

- About migrating to a cloud platform: https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/about-migrating-to-automation-cloud
- Using the Automation Cloud Migration Tool: https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/using-the-migration-tool
- Manual migration: https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/manual-migration
- Robot connectivity (cloud): https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/connecting-robots-to-orchestrator
- Robot Command Line Interface: https://docs.uipath.com/robot/standalone/latest/admin-guide/command-line-interface
- Activating your Enterprise license: https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/activating-your-license
- License migration: https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/license-migration
- Configuring the firewall for Automation Cloud (FQDN allowlist, unified IP ranges, Sept 2026 transition): https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/configuring-the-firewall-for-cloud
