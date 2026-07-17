# Standalone Orchestrator — Upgrade Guide

## Scope
Upgrading an existing Standalone Orchestrator installation to a newer version.
Covers in-place upgrade (same server) and side-by-side upgrade (new server).

---

## Upgrade Path Rules (CRITICAL)

**Never skip LTS versions.** Always upgrade through the LTS chain:

```
2021.10 → 2022.10 → 2023.10 → 2024.10   ✅ Correct
2021.10 → 2024.10                          ❌ Not supported
2022.4  → 2023.4  → 2024.10               ✅ Correct
```

**Robot/Studio compatibility with the upgraded Orchestrator:**
- For **Standalone Orchestrator**, UiPath's own compatibility matrix shows full cross-compatibility —
  every Robot version from 2021.10 through the latest release is compatible with every Standalone
  Orchestrator version in that matrix. There is **no forced Robot/Studio version bump** just because
  Orchestrator was upgraded, and no "1 version behind / can't be ahead" rule for Standalone.
  Recommended order is still: upgrade Orchestrator first, then Robots, and reconnect Robots to
  Orchestrator afterward — but that's a practical recommendation, not a hard compatibility requirement.
- **Studio and Robot must match each other's version** when installed on the same machine
  (e.g. Studio 2023.10.x needs Robot 2023.10.x on that box) — this is independent of the
  Orchestrator version.
- This full cross-compatibility is a **Standalone-only** rule. Automation Cloud is different — it
  only guarantees backward compatibility with the **three latest enterprise Robot/Studio releases**;
  anything older is unsupported there and must be upgraded regardless of the Orchestrator side.

📖 https://docs.uipath.com/robot/standalone/latest/admin-guide/about-backward-and-forward-compatibility
📖 Before relying on this for a specific pair of versions, also confirm against the official upgrade-path guidance for the target release: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/about-updating-and-migrating

---

## Pre-Upgrade Checklist

### Official steps (per UiPath's "Before you upgrade" guide)

- [ ] **Only relevant if your CURRENT version predates 2023.10: confirm no Classic folders/robots remain before upgrading to a 2023.10+ target.**
  This check only applies the first time you cross the 2023.10 line. If you're already running
  2023.10 or later today (e.g. upgrading 2023.10 → 2024.10, or 2023.x → 2025.x), Classic folders
  cannot exist on your system — they would have had to be migrated away already just to reach
  your current version — so there is nothing to check here and this step doesn't apply.
  For a customer still on a pre-2023.10 version (2021.10, 2022.4, 2022.10, or 2023.4) targeting
  2023.10 or later for the first time: this is a hard blocker, not a recommendation —
  Orchestrator 2023.10+ setup stops with
  `This Orchestrator version does not support Classic Folders and Classic Robots...` if any
  classic objects are still in the database. Migrate them to Modern folders and delete the
  classic folders **before** starting this upgrade — see `references/classic-to-modern-folders.md`.
  This is listed as an explicit numbered step in UiPath's own pre-upgrade guidance, not just a
  best practice. Do this check first, before anything else below, since it may add a whole
  migration project ahead of the upgrade itself.
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/before-you-upgrade
- [ ] **Back up your Orchestrator database.**
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/backup-and-restore
- [ ] **Run the pre-upgrade Identity Server cleanup script** (removes expired/consumed
  `[identity].[PersistedGrants]` rows to speed up the primary key/index rebuild during
  migration) — see the exact script in the SQL Maintenance section below.
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/before-you-upgrade

### Additional practical checks

- [ ] **Backup all config files:**
  ```
  C:\Program Files (x86)\UiPath\Orchestrator\UiPath.Orchestrator.dll.config
  C:\Program Files (x86)\UiPath\Orchestrator\Identity\appsettings.Production.json
  C:\Program Files (x86)\UiPath\Orchestrator\Webhooks\appsettings.Production.json
  C:\Program Files (x86)\UiPath\Orchestrator\ResourceCatalog\appsettings.Production.json
  C:\Program Files (x86)\UiPath\Orchestrator\web.config
  ```
- [ ] **Back up all NuGet package directories**
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-backup-and-restore
- [ ] **Note current version** (Help → About in Orchestrator portal)
- [ ] **Note SSL certificate thumbprint** (certlm.msc → Personal → Certificates)
- [ ] **Confirm SQL account** still has `db_owner` on the Orchestrator database
- [ ] **Confirm the ASP.NET Core Hosting Bundle version required by the target release** —
  this has genuinely changed across releases, don't assume last engagement's version still applies:
  | Orchestrator version | ASP.NET Core Hosting Bundle required |
  |---|---|
  | 2023.10 | 6.0.x **or** 8.0.x |
  | 2024.10 | confirm on the live Software Requirements page for that release — matrix shifts |
  | 2025.10 | **8.0.x only** — 6.0.x support has been dropped |
  If the customer is currently on 6.0.x and the target is 2025.10 (or any release that dropped 6.0.x),
  the Hosting Bundle upgrade is a **mandatory pre-upgrade step**, not optional — check the exact
  version required by the target release, don't assume.
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-software-requirements
  📖 https://docs.uipath.com/orchestrator/standalone/2025.10/installation-guide/orchestrator-software-requirements
- [ ] **Notify users** — schedule a maintenance window (Orchestrator will be down while the
  installer runs and the database migrates; duration depends on DB size)
- [ ] **Stop all active Robot jobs** (or wait for completion)
- [ ] **Confirm license** covers the target version

---

## Legacy / Automation Project Compatibility

If the plan also involves upgrading Studio (see Robot/Studio compatibility above), check existing
automation projects before rolling out:

- **Backward compatible:** a project built in an older Studio version runs fine on a newer Robot
  (e.g. a project from Studio 2023.4 runs on a 2024.10 Robot).
- **NOT forward compatible:** UiPath does not support forward compatibility — a project published
  with a *newer* Studio/CLI may not run on an *older* Robot (e.g. a project from Studio 2024.10 may
  not run on a 2023.4 Robot). Projects opened or created in a newer Studio version also cannot be
  reliably opened with older Studio versions.
- Practical implication: if this upgrade also bumps Studio, any project republished with the new
  Studio needs to be validated against the current Robot fleet before rollout — don't assume it
  "just still works" because the Orchestrator/Robot side upgraded cleanly.

📖 https://docs.uipath.com/robot/standalone/latest/admin-guide/about-backward-and-forward-compatibility

---

## Step-by-Step Upgrade Checklist

### Phase 1 — Pre-Upgrade

- [ ] **1.1** Take SQL database backup (see above)
- [ ] **1.2** Run the pre-upgrade Identity Server cleanup script (see SQL Maintenance section)
- [ ] **1.3** Copy config file backups to a safe location off the server
- [ ] **1.4** If upgrading .NET/ASP.NET Core Hosting Bundle version — install the correct new
  Hosting Bundle first, run `IISRESET`
- [ ] **1.5** Download the new version MSI from UiPath Customer Portal
- [ ] **1.6** Stop IIS to prevent new connections during upgrade:
  ```cmd
  iisreset /stop
  ```

### Phase 2 — Run Upgrade MSI

- [ ] **2.1** Right-click new MSI → Run as Administrator
- [ ] **2.2** Installer detects existing installation — confirms upgrade mode
- [ ] **2.3** Verify database connection string is pre-populated correctly
- [ ] **2.4** Click **Test Connection** — must succeed
- [ ] **2.5** Proceed with upgrade — installer runs DB migrations automatically
- [ ] **2.6** Wait for completion (time varies with DB size — the PersistedGrants cleanup in
  Phase 1 exists specifically to keep this step fast)
- [ ] **2.7** Installer restarts IIS automatically at completion

📖 Full step-by-step for both single-node and multi-node (primary/secondary) upgrades:
https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/updating-using-the-windows-installer

### What "rollback" actually means for this MSI — read before the upgrade window, not after a failure

A common assumption is: "if the upgrade fails, just reinstall the old MSI and you're back to the
previous version." This is **only half true**, per internal engineering analysis of the MSI upgrade
code path:

- The Orchestrator MSI can cleanly roll back the **application binaries** if the install itself
  fails partway through.
- It does **not** automatically roll back the **database**. The EF Core database migration step
  (`UiMigrator.cs`) runs outside a suppressed/rollback-safe transaction scope, and the command
  handler that applies it has no built-in rollback logic. Once the migration has committed,
  reinstalling the previous MSI does not undo the schema changes.
- Specific migrations (several introduced around the 24.10 line) are **destructively irreversible**
  at the schema level — there is no "undo" once they've run, MSI reinstall or not.

**Practical implication:** the only reliable rollback path is restoring the pre-upgrade SQL backup
taken in Phase 1 — not "reinstall the old MSI and expect the database to follow." Confirm before
the maintenance window starts (not after a failure) that: the SQL backup is taken immediately
before the upgrade begins, and someone on the call actually knows how to restore it.
📖 Internal engineering reference: "Upgrade Rollback - Orchestrator MSI: Official Claim vs Reality"
(UiPath internal Confluence)

### Phase 3 — Post-Upgrade Validation

- [ ] **3.1** Verify IIS Application Pools all show **Running**

- [ ] **3.2** Re-check SSL thumbprint in Identity config (upgrade sometimes resets this):
  ```json
  // C:\Program Files (x86)\UiPath\Orchestrator\Identity\appsettings.Production.json
  "Thumbprint": "<verify matches cert in certlm.msc>"
  ```

- [ ] **3.3** Run Platform Configuration Tool to validate setup:
  ```powershell
  cd "C:\Program Files (x86)\UiPath\Orchestrator\Tools\PlatformConfiguration"
  .\Platform.Configuration.Tool.ps1
  ```
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/platform-configuration-tool

- [ ] **3.4** Access Orchestrator in browser — confirm version number updated

- [ ] **3.5** Test login (Host admin + Tenant user)

- [ ] **3.6** Run a test Robot job end-to-end

- [ ] **3.7** Restart all Robots so they pick up the new settings (recommended post-upgrade step)

- [ ] **3.8** Check Windows Event Viewer for new errors post-upgrade:
  ```
  Windows Logs → Application → Filter by time (since upgrade started)
  ```

- [ ] **3.9** If the customer upgraded or uninstalled a Solution (multi-process) package as part
  of this change, spot-check that package versions are still present under folder-hierarchy feeds.
  A confirmed (now-fixed) internal bug could delete the correct package version from a
  folder-hierarchy feed as a side effect of a Solution upgrade/uninstall step — worth a quick check
  on builds that predate the hotfix rather than assuming the feed is intact just because the
  upgrade "succeeded."
  📖 Internal reference: "External RCA: Orchestrator package version deleted after solution upgrade"
  (UiPath internal Confluence, Site Reliability space)

---

## Upgrade-Specific Common Errors

| Error | Cause | Fix |
|---|---|---|
| `HTTP Error 500.37` after upgrade | .NET/ASP.NET Core Hosting Bundle version mismatch | Install the Hosting Bundle version required by the target release (check Software Requirements page); IISRESET |
| `MetadataAddress must use HTTPS` | Thumbprint reset during upgrade | Update thumbprint in `Identity\appsettings.Production.json` |
| `Invalid issuer` login error | PublicUrl changed or identity config mismatch | Run Platform Config Tool with correct URL |
| DB migration takes a very long time / times out | Large `[identity].[PersistedGrants]` table not cleaned up before upgrade | Run the pre-upgrade PersistedGrants cleanup script (see below) *before* starting the upgrade, not after |
| Robots show `Disconnected` post-upgrade | Machine key changed or URL mismatch | Re-register robots with new machine key from Orchestrator |
| `Object reference not set` on Webhooks | Webhooks config not updated | Restore Webhooks `appsettings.Production.json` from backup |

📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-installation-troubleshooting

---

## Multi-Node, High Availability (HAA), and DR Upgrade Considerations

**Important scoping note:** per UiPath's own Multi-Node Deployment page, multi-node Orchestrator
deployments are only officially supported if the High Availability Add-on (HAA) is used. If a
customer genuinely has 2+ nodes concurrently serving live traffic without HAA, that is an
unsupported configuration — flag it, don't just assume it's a normal setup.
📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/multi-node-deployment

### Topology 1 — Active/Passive *without* HAA (simple standby — not the same as UiPath's documented "Active/Passive DR" model below)

What this usually means in practice: one Orchestrator node actively serves all traffic; a second
node is installed but sits idle/passive, brought online only on failover (e.g. via Windows
Failover Clustering, or a manual DNS/NLB cut-over). Because only one node is ever live at a time,
there's no concurrent shared-cache/SignalR correctness problem, so HAA (Redis) isn't required —
this is a different, simpler pattern than UiPath's own "Disaster Recovery - Active/Passive"
architecture covered under Topology 2, which **does** require HAA.

Upgrade approach:
- [ ] Take the passive node out of any failover/cluster rotation first, so it can't accidentally
  receive traffic mid-upgrade.
- [ ] Upgrade the active (primary) node exactly like a single-node upgrade (see the Step-by-Step
  Upgrade Checklist above) — this is what runs the DB migration.
- [ ] Once the active node is confirmed healthy on the new version, upgrade the passive node's
  Orchestrator installation to match — it must never be left on an older version than the
  now-migrated DB schema.
- [ ] Only re-enable the passive node in the failover/cluster configuration once **both** nodes
  are confirmed on the identical version.
- Do not let any old-version node point at the already-migrated (new-version) database at any
  point, even briefly — mixed versions sharing one DB is not supported.

### Topology 2 — Officially documented multi-node upgrade (HA, Active/Passive DR, and Active/Active DR — all require HAA)

This is UiPath's own documented process. It applies equally to: a standard multi-node HA
deployment, the **Active/Passive DR** model (HA in the primary datacenter plus a reduced DR
datacenter, with HAA installed in CRDB mode), and the **Active/Active "Two Active Data Centers"**
model (both datacenters live simultaneously, NLB round-robins traffic between them, requires 2
HAA licenses plus a SQL Server Always On Availability Group spanning both datacenters).
📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/disaster-recovery-activepassive
📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/disaster-recovery-two-active-data-centers

UiPath does not document a rolling/zero-downtime upgrade path for any of these — plan for a full
maintenance window across every node, not a staggered rollout:

- [ ] **1.** Back up automation packages, `web.config`, `UiPath.Orchestrator.dll.config`, and the
  database — same as any upgrade.
- [ ] **2. Primary node first, and only once.** Run the installer on the primary node:
  ```cmd
  :: Attended
  UiPathOrchestrator.msi OUTPUT_PARAMETERS_FILE=c:\temp\upgradeParams.json /lvx* upgrade.log

  :: Unattended
  UiPathOrchestrator.msi PUBLIC_URL=https://hostname.local APPPOOL_USER_NAME=serviceAccount APPPOOL_PASSWORD=pass OUTPUT_PARAMETERS_FILE=c:\temp\upgradeParams.json /lvx* upgrade.log /Q
  ```
  This is what actually runs the DB migration — it must happen exactly once, on the primary node
  only. **Save the generated `upgradeParams.json`** — every secondary node's install depends on it.
- [ ] **3. Then every secondary node**, using the params file produced by the primary:
  ```cmd
  UiPathOrchestrator.msi SECONDARY_NODE=1 PARAMETERS_FILE=c:\temp\upgradeParams.json /lvx* upgrade.log /Q
  ```
  Repeat for each secondary/HA node. None of them re-run the DB migration — they join the schema
  the primary node already migrated.
- [ ] **4. Flush HAA cache keys** once every node is on the new version:
  - Single-region HAA (standard HA, or the Active/Passive DR model within one HAA cluster):
    ```
    redis-cli -h <hostname> -p <portnumber> -a <password> flushall
    ```
    (HAA uses port `10000` by default.)
  - Active-Active CRDB (the geo-replicated Two-Active-Data-Centers model):
    ```
    crdb-cli crdb flush --crdb-guid <guid> [--no-wait]
    ```
  Skipping this step is a common cause of stale cache/permission issues right after a multi-node
  upgrade.
- [ ] **5.** Restart all Robots afterward so they reconnect against the fully upgraded cluster.

**Note:** although the installer prompts for host/default-tenant admin passwords during a
secondary-node install, they're not actually applied — keep using your existing passwords to log
in afterward.

📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/updating-using-the-windows-installer

**Real-world implication for a "2023.x → 2025.x" scenario:** none of the sequencing above changes
based on target version — primary-then-secondary ordering and the flush step are identical
regardless of which versions you're moving between, as long as it's a supported LTS-chain hop
(see Upgrade Path Rules above). What *does* change per-version is everything else already covered
in this guide — the .NET/Hosting Bundle requirement, Classic folder scoping, and DB maintenance.

---

## SQL Maintenance — Recommended Before Upgrade

**This is an official, documented pre-upgrade step** — not an optional nice-to-have. UiPath's
own "Before you upgrade" guidance is exactly: (1) back up the database, (2) run this cleanup
script, (3) migrate Classic folders to Modern folders if any remain.

### Step 1 — Clean up Identity Server's PersistedGrants table

This removes expired/consumed grants, which speeds up the `[identity].[PersistedGrants]`
primary key and index rebuild during the upgrade's database migration. This is the exact
script UiPath publishes for this purpose:

```sql
DECLARE @Now DATETIME2 = GETUTCDATE()
DECLARE @ConsumedGrantsGracePeriod DATETIME2 = DATEADD(hour, -2, @Now)

DECLARE @ConsumedDeleted int = 1
DECLARE @ExpiredDeleted int = 1
DECLARE @BatchSize int = 500
DECLARE @ConsumedBatchesDeleted int = 0
DECLARE @ExpiredBatchesDeleted int = 0

SET LOCK_TIMEOUT 0
SET DEADLOCK_PRIORITY LOW

WHILE (@ConsumedDeleted=1 OR @ExpiredDeleted=1)
BEGIN
  IF @ConsumedDeleted=1
  BEGIN
    BEGIN TRY
      DELETE TOP(@BatchSize) FROM [identity].[PersistedGrants] WHERE [ConsumedTime] IS NOT NULL AND [ConsumedTime] < @ConsumedGrantsGracePeriod AND [Type] <> 'reference_token'
      IF @@ROWCOUNT = 0 SET @ConsumedDeleted=0
      ELSE SET @ConsumedBatchesDeleted = @ConsumedBatchesDeleted + 1
    END TRY
    BEGIN CATCH
      PRINT 'Failed to delete consumed grants'
    END CATCH
  END
  IF @ExpiredDeleted=1
  BEGIN
    BEGIN TRY
      DELETE TOP(@BatchSize) FROM [identity].[PersistedGrants] WHERE [Expiration] < @Now AND [Type] <> 'reference_token'
      IF @@ROWCOUNT = 0 SET @ExpiredDeleted=0
      ELSE SET @ExpiredBatchesDeleted = @ExpiredBatchesDeleted + 1
    END TRY
    BEGIN CATCH
      PRINT 'Failed to delete expired grants'
    END CATCH
  END
  IF (@ExpiredDeleted=1 OR @ConsumedDeleted=1)
    WAITFOR DELAY '00:00:05.000'
END
```

📖 Source (exact script, verify against your target version): https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/before-you-upgrade

### Step 2 — General database cleanup (Logs, Jobs, QueueItems, etc.)

For large `dbo.Logs` / `dbo.Jobs` / `dbo.QueueItems` tables, do **not** write ad-hoc DELETE
loops — UiPath publishes a maintained cleanup framework for exactly this, downloadable from
the Customer Portal:

- `CreateOrchestratorCleanupObjects.sql` creates `dbo.__CleanupLog`, `dbo.GetOrCreateArchiveTable`,
  and `dbo.RunOrchestratorCleanup` — then you run `dbo.RunOrchestratorCleanup` with an XML
  config describing what to clean up and how long to keep.
- A PowerShell equivalent (`RunOrchestratorCleanup.ps1`) exists for environments where you
  can't run SQL scripts directly.
- **You do not need to upgrade or replace these scripts each time Orchestrator is upgraded** —
  per UiPath's own note, they continue to function as expected across Orchestrator versions.
  This is a recurring maintenance job (schedule it, e.g. via SQL Server Agent), not a one-time
  pre-upgrade task — but running it before an upgrade specifically shrinks the tables the
  upgrade's own DB migration has to touch, which is why it's called out here.
- For very high-volume Robot logging, UiPath's own recommendation is to write Robot logs
  directly to **Elasticsearch** instead of the SQL `Logs` table once volumes get large — see
  the "Write Robot Logs to Elasticsearch" section of the Performance Best Practices page. There
  is no single official row-count threshold published for when to do this — treat it as a
  capacity-planning decision for your environment, not a fixed number.

**Which tables the recommended cleanup config actually covers, and why each one matters**
(this is UiPath's own preconfigured `CleanupConfig` XML, not a partial list — every table below
is named explicitly in the official sample):

| Table | Default retention | What it stores / why it needs cleanup |
|---|---|---|
| `QueueItems` | 180 days (only terminal states — Successful/Failed/Abandoned/etc.) | One row per transaction item ever added to a queue. Usually the single biggest driver of DB growth in any environment with unattended queue processing. |
| `Jobs` | 180 days (only terminal states — Stopped/Faulted/Successful) | One row per Robot job execution. Grows fast with large unattended fleets or high job-trigger frequency. |
| `Logs` | 90 days | One row per log message emitted by every running process (Info/Warn/Error/Trace). Typically the **fastest-growing table by far** — this is the table behind UiPath's advice to offload Robot logs to Elasticsearch at scale. |
| `AuditLogs` | 365 days | Records administrative and user actions inside Orchestrator (who changed what, when) — kept longer by default because it's the compliance/security audit trail. |
| `Tasks` | 180 days (only soft-deleted rows, `IsDeleted = 1`) | Action Center human-in-the-loop task records. |
| `QueueProcessingRecords` | 30 days | Queue throughput/reporting statistics, not the queue items themselves. |
| `Sessions` | 180 days | Robot/Unattended session heartbeat records. |
| `RobotLicenseLogs` | 180 days | License usage history per Robot — useful for license audits, not needed indefinitely. |
| `UserNotifications` / `TenantNotifications` | 90 days | In-app notification bell items — purely UI convenience data. |
| `Ledger` / `LedgerDeliveries` | 7 days | Short-lived internal event/webhook delivery bookkeeping — cleared quickly by design. |
| `Assets` | 120 days (only soft-deleted rows, `IsDeleted = 1`) | Deleted asset records kept briefly for recovery, then purged. |
| `__CleanupLog` | 7 days | The cleanup script's own execution log — self-pruning. |

Each row can be independently tuned (or disabled) in the XML config — the table above reflects
UiPath's **recommended defaults**, not hard limits.

📖 Full script downloads + XML config reference: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/maintenance-considerations
📖 Elasticsearch offload guidance for high-volume Robot logs: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/performance-best-practices

**Note:** there is no `[identity].[Logs]` table — Identity Server's own maintenance page
covers a separate table, `[identity].UserLoginAttempts`, with its own archive-then-delete
approach:
- Recommended: create a separate archive database first (e.g. `UiPathIdentityArchives`) with
  an `ArchiveUserLoginAttempts` table matching the source schema, so old rows are preserved
  for audit purposes before being deleted from the live table.
- UiPath's own example script deletes/archives `UserLoginAttempts` rows older than **60 days**
  (configurable via the `@NumberOfDaysToKeep` variable in the script) — this table logs every
  login attempt (success and failure), so it grows continuously with user/robot sign-in volume.
📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/is-maintenance-considerations

---

## Reference Links

- Before you upgrade (official pre-upgrade steps): https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/before-you-upgrade
- Updating using the Windows Installer: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/updating-using-the-windows-installer
- Backup and Restore overview: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/backup-and-restore
- Orchestrator database maintenance (log/data cleanup scripts): https://docs.uipath.com/orchestrator/standalone/2022.10/installation-guide/maintenance-considerations
- Identity Server maintenance: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/is-maintenance-considerations
- Software Requirements (Hosting Bundle version per release): https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-software-requirements
- Classic folders removal impact on upgrades: https://docs.uipath.com/overview/other/latest/overview/classic-folders-removal
