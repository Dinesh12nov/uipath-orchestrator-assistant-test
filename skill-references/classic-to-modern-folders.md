# Orchestrator — Migrating Classic Folders to Modern Folders

## Scope
Migrating an existing Standalone or Automation Cloud tenant from Classic folders (environment-based,
manually managed users/robots) to Modern folders (hierarchical, AD-integrated, auto-provisioned).
Covers the built-in migration wizard, post-migration cleanup, rollback, and the hard removal of
Classic folders in Orchestrator 2023.10+.

---

## Why This Matters Now

Classic folders are not just deprecated — they are **removed outright** starting with Orchestrator
2023.10. Timeline:

- Oct 2021 — deprecation announced
- Apr 2022 — removal announced
- Oct 2022 — migration wizard launched
- Apr 2023 — executions disabled in classic folders
- Oct 2023 — classic folders removed entirely from 2023.10+

**If a customer upgrades to 2023.10+ with any classic objects still in the database, setup stops with:**
`This Orchestrator version does not support Classic Folders and Classic Robots. Please migrate your
installation to Modern Folders, delete your existing Classic Folders before upgrading.`

So this is mandatory, not optional, for any pre-2023.10 customer planning to upgrade.

---

## Classic vs Modern — What Changes

| Feature | Classic Folders | Modern Folders |
|---|---|---|
| AD as central hub for user info | Available | Available |
| SSO with AD credentials | Available | Available |
| Automatic Robot Management | Not available | Available |
| Automatic License Assignment | Not available | Available |
| Hierarchical Folder Structure | Not available | Available |
| Fine-Grained Permissions | Not available | Available |
| Job Restart | Available | Available |
| Long-Running Workflows | Available | Available |

---

## Prerequisites Checklist

- [ ] Confirm you are an **organization administrator** in Automation Cloud
- [ ] Confirm your account has these permissions: Roles (View/Create/Edit), Settings (View/Edit), Users (View/Create/Edit), Robots (View/Create/Edit/Delete), Folders (Create/Edit)
- [ ] Count classic robots in scope — **do not use the wizard above ~2,000 classic robots per folder set**; large deployments need a dedicated migration strategy instead
- [ ] Add yourself to **every classic folder** you want migrated — folders you're not assigned to are silently skipped
- [ ] Confirm every robot you want migrated is added to an **environment** — robots not in any environment are presumed unused and skipped
- [ ] Review the Automation Users group — remove elevated roles/extra licenses before migrating, since attended users/robot accounts auto-inherit Automation Users role at folder level post-migration
- [ ] Confirm attended-robot usernames contain `@` (i.e. are directory users, not local users) — local users block migration (see Common Errors)
- [ ] Make sure **no jobs are running** and disable any triggers that might fire during the migration window

---

## Step-by-Step Migration Checklist (Wizard)

### Phase 1 — Getting Started
- [ ] **1.1** Go to Tenant → Settings (opens on the General tab)
- [ ] **1.2** In the Classic Folders section, click **Start migration** — opens the Modern migration wizard
- [ ] **1.3** Review the Summary section, click **Copy the summary above**, and save it for your records
- [ ] **1.4** Click **Next** to move to the Attended users step

### Phase 2 — Attended Users
- [ ] **2.1** For each attended robot found, select the correct **Target user account**
- [ ] **2.2** For any unmapped/incorrect account: click **Assign** → search for the user → **Save**
- [ ] **2.3** Click **Next** to move to the Unattended users step

### Phase 3 — Unattended Users
- [ ] **3.1** Under Bulk Actions, choose how to handle unmapped classic unattended robots — **Automatically generate robot accounts** (recommended) or **Ignore them** (not recommended)
- [ ] **3.2** Review the Target robot account column for correctness
- [ ] **3.3** If you chose "Ignore them," manually map remaining robots via Assign, or create new robot accounts
- [ ] **3.4** Click **Next** to reach the Finishing page

### Phase 4 — Execute
- [ ] **4.1** Click **Execute migration** to start
- [ ] **4.2** Confirm in the dialog by clicking **Execute**
- [ ] **4.3** Watch per-folder progress; if any folder fails, read its error message, fix the underlying issue, then restart or retry that folder
- [ ] **4.4** Click **Close** to exit the wizard once successful
- [ ] **4.5** Wait ~10 minutes after completion for the wizard to disable robots in migrated classic folders and release licenses back for modern-folder use

---

## Post-Migration Setup (Required — Not Automatic)

Robots and Environments do **not** need re-provisioning. Everything else below does:

- [ ] Recompile workflows using Orchestrator activities or direct HTTP calls to the Orchestrator API against **UiPath.System.Activities 2019.10+** — migrated workflows only run on 2019.10+ Robots
- [ ] Re-provision other entities (e.g. action catalogs) in the corresponding modern folder
- [ ] Unlink Test Sets from classic folders (delete from the corresponding Test Manager projects)
- [ ] Re-link Test Sets by selecting the ones marked **[Migrated]** in their description
- [ ] Update any UiPath Apps referencing the old classic-folder process to point at the migrated modern-folder process
- [ ] Update workflows using **Start Job** with the old `processName_envName` syntax to just `processName` (modern folders don't use environments)
- [ ] Enable **interactive sign-in** for the tenant if not already on — this is mandatory in modern folders
- [ ] Test unattended processes via Start Job from Orchestrator in the new modern setup
- [ ] Upgrade end-user workstations to **UiPath Robot 2019.10+**
- [ ] Remove the now-unused classic folders once everything is validated

---

## Reverting to Classic Folders (Rollback)

If something goes wrong post-migration and you need to roll back:

- [ ] Set the tenant's robot authentication settings back to **Hybrid**
- [ ] Re-enable all classic robots
- [ ] Re-enable triggers in classic folders
- [ ] Delete the newly created modern folders
- [ ] Delete the newly created robot accounts
- [ ] Investigate the root cause in the classic setup before re-attempting
- [ ] Re-run the migration once the root cause is resolved

---

## Common Errors & Fixes

| Error / Symptom | Cause | Fix |
|---|---|---|
| `This Orchestrator version does not support Classic Folders and Classic Robots...` | Upgrading to 2023.10+ with classic objects still present | Migrate all classic folders to modern, delete remaining classic folders, then retry the upgrade |
| Migration fails related to jobs not reaching final state | A terminated job stayed in `Terminating` instead of reaching `Stopped` | Wait — after 24h stuck `Terminating` jobs auto-flip to `Stopped`, then restart the migration |
| Migration fails for Test Data Queues / duplicate items on retry | Partially-migrated data left over from a prior failed attempt | Check **Clean-up before retrying** before restarting the migration |
| Migration does not succeed for a given attended robot | Robot's username has no `@` — it's a local user, not a directory user | Convert to a directory user (usually automatic on next login) or run the documented SQL fix against `dbo.Users` / `dbo.UserLogins` |
| Robot mapping/creation fails for a specific robot | Migrated robot name exceeds the 64-character limit | Manually create the robot account and map it yourself |
| Robot connects with the wrong/unexpected username after migration | Multiple attended robots were mapped to the same target account — the wizard picks one username at random | Manually verify and fix the machine connection credentials per robot |
| Queue trigger can't be edited mid-migration | Editing classic-folder queue triggers is blocked from the moment migration starts until it completes | Wait for migration to finish (or fail/rollback) before editing that trigger |

---

## Reference Links

- Migrating From Classic to Modern Folders: https://docs.uipath.com/orchestrator/standalone/2023.4/user-guide/migrating-from-classic-folders-to-modern-folders
- Classic Folders Vs Modern Folders: https://docs.uipath.com/orchestrator/standalone/2023.4/user-guide/classic-folders-vs-modern-folders
- Classic Folders Removal (timeline & 2023.10+ impact): https://docs.uipath.com/overview/other/latest/overview/classic-folders-removal
