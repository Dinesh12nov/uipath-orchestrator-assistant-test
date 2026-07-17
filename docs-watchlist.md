# UiPath Docs Watch-list — daily change check

The daily routine fetches the **priority** URLs below and compares the current live
guidance against the baseline guides in `skill-references/`. It reports what changed
and proposes edits — it never publishes on its own (review-first).

Baseline guides (what "current" is compared against), readable at:
`https://raw.githubusercontent.com/Dinesh12nov/uipath-orchestrator-assistant/main/skill-references/<file>.md`

---

## Priority pages (check daily) — highest signal, change most often

### Versions / requirements / compatibility (drive upgrade + install guidance)
- https://docs.uipath.com/orchestrator/standalone/2025.10/installation-guide/orchestrator-software-requirements
- https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-software-requirements
- https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/before-you-upgrade
- https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/about-updating-and-migrating
- https://docs.uipath.com/robot/standalone/latest/admin-guide/about-backward-and-forward-compatibility
- https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/compatibility-matrix

### High availability / DR (upgrade topology guidance)
- https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/disaster-recovery-activepassive
- https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/disaster-recovery-two-active-data-centers

### Cloud migration (tool scope, what's not migrated, firewall/IP deadline, license)
- https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/using-the-migration-tool
- https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/manual-migration
- https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/configuring-the-firewall-for-cloud
- https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/license-migration

### Classic → Modern folders (removal timeline + wizard)
- https://docs.uipath.com/overview/other/latest/overview/classic-folders-removal
- https://docs.uipath.com/orchestrator/standalone/2023.4/user-guide/migrating-from-classic-folders-to-modern-folders

### Credential stores (onboarding guide)
- https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores

### Automation Suite (install/upgrade)
- https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/installing-automation-suite
- https://docs.uipath.com/automation-suite/automation-suite/2024.10/installation-guide-eks-aks/upgrading-automation-suite

---

## Mapping: which guide each priority page backs
| Page theme | Baseline guide file |
|---|---|
| Software requirements / before-you-upgrade / DR / compatibility | `standalone-upgrade.md`, `standalone-install.md` |
| Migration tool / manual migration / firewall / license | `cloud-migration.md` |
| Classic folders removal / wizard | `classic-to-modern-folders.md` |
| Credential stores | `cloud-onboarding.md` |
| Automation Suite install/upgrade | `automation-suite.md` |

---

## Full cited URL set (reference — not all checked daily)
See the "Reference Links" section at the bottom of each file in `skill-references/`.
There are ~85 cited URLs total; the priority list above is the high-signal subset.
