# Automation Cloud — Multi-Tenant Onboarding & Credential Stores

## Scope
Onboarding new tenants/branches to Automation Cloud (including APAC multi-country patterns),
and configuring credential stores (CyberArk CCP, Azure Key Vault, HashiCorp Vault, BeyondTrust).

---

## Multi-Tenant Onboarding Checklist

> The real portal flow is: **Admin → Tenants view → click the "+" (plus) icon → Create new tenant**
> (General step → Region/plan step → review). Exact menu labels can shift between UI releases, so
> treat the steps below as a checklist of *what* to configure, not a pixel-accurate click-path — verify
> against the live product. 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/managing-tenants
> 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/about-tenants
>
> Note: creating additional tenants is a **Flex Pro / Enterprise** capability — Community and Free Flex
> organizations are limited to the single auto-created `DefaultTenant`.

### New Tenant Setup

- [ ] **1.1** Admin → Tenants → "+" (Add Tenant)
  - Name: use consistent naming convention (e.g., `APAC_Singapore`, `EMEA_London`); up to 32
    alphanumeric characters, starting with a letter, no spaces/special characters
  - Region: select closest region available on your plan
- [ ] **1.2** Assign licenses to new tenant:
  - Admin → select tenant → allocate licenses for the services you provision
  - Allocate: Unattended Robot, Attended Robot, Studio seats as required
  - 📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/allocating-licenses-to-tenants
- [ ] **1.3** Configure SSO for tenant (if using Azure AD / Entra ID per-country):
  - Check current Admin navigation for external identity provider / SSO configuration — this has moved
    across UI releases, so confirm the exact path in the live portal rather than relying on a fixed
    click-path here
  - Add your external IdP with the correct Tenant ID for that country's AD
- [ ] **1.4** Create Folder structure:
  - Follow naming convention: `<Country>/<BU>/<Environment>`
  - e.g., `SG/Finance/Production`
- [ ] **1.5** Create Machine Templates for the tenant's Robot machines
- [ ] **1.6** Add Robot user accounts (Directory or Local)
- [ ] **1.7** Configure credential store (see below)
- [ ] **1.8** Upload packages / create processes
- [ ] **1.9** Test end-to-end Robot connectivity and job execution

### Tenant Isolation Considerations

| Setting | Recommendation |
|---|---|
| Folder permissions | Scope strictly to tenant's own folders |
| Credential stores | Configure per-tenant (not shared across tenants) — **this matters even for the same third-party vault**: UiPath's own CyberArk CCP docs warn that a CyberArk store configured in multiple tenants with the *same* App ID, Safe, and Folder Name will permit cross-tenant access to the same stored credentials. Use distinct App ID/Safe/Folder combinations per tenant. 📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores#cyberark-ccp |
| Packages | Use separate feeds per tenant or folder-level access control |
| SSO | Per-country identity provider tenants if different domains |
| Robots | Machine templates scoped to tenant folders |

---

## Credential Store Setup Guides

> Third-party credential stores (Azure Key Vault, CyberArk, HashiCorp Vault, BeyondTrust, etc.) require
> **Enterprise – Advanced** (Flex Pricing) or **Enterprise / Application Test Enterprise** (Unified
> Pricing) licensing. 📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores
>
> Real navigation to add any store: **Orchestrator → (Tenant context) → Credentials → Stores tab →
> "Add credential store"** → pick a **Type** in the dialog. 📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores#creating-a-credential-store

### Option 1 — Azure Key Vault (Most Common for Cloud)

**Required Azure permissions for the SPN/App Registration:**

Confirmed against UiPath docs — Azure Key Vault credential stores use Azure RBAC authentication, and
the role assigned to the service principal depends on store type:

| Mode | Required Azure RBAC Role |
|---|---|
| Read-Only (`Azure Key Vault (read-only)` store type) | **Key Vault Secrets User** |
| Read-Write (`Azure Key Vault` store type) | **Key Vault Secrets Officer** |

📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/integrating-credential-stores#azure-key-vault-integration

**Azure Setup:**
```
1. Azure Portal → App Registrations → New Registration
2. Note: Application (Client) ID
3. Create Client Secret (Manage → Certificates & Secrets → New client secret)
   → Note the secret Value immediately (only shown once)
4. Azure Portal → Key Vaults → [Your Vault] → Overview
   → Copy Vault URI and Directory ID for later use
5. Access Control (IAM) → Add → Add role assignment
   → Role: "Key Vault Secrets Officer" (for the read-write store)
      OR "Key Vault Secrets User" (for the read-only store)
   → Assign the role to the service principal of your App Registration
   → Review + assign
```
*(No redirect URI is required for this flow — Key Vault access uses the app registration's client
credentials, not an interactive OAuth redirect. The original draft's "callback" redirect URI step was
not found in UiPath or Microsoft documentation and has been removed as unverifiable.)*

**Orchestrator Setup:**
```
1. Orchestrator → Tenant → Credentials → Stores tab → Add credential store
2. Type: Azure Key Vault (read-write) OR Azure Key Vault (read-only)
3. Name: <descriptive name for this store>
4. Key Vault Uri: https://<vault-name>.vault.azure.net/
5. Directory ID: <Directory/Tenant ID from the Key Vault Overview page>
6. Client Id: <Application (Client) ID from Azure AD App Registration>
7. Client Secret: <Secret value>
8. Select Create — Orchestrator validates and creates the store
```
📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores#azure-key-vault

**Validate SPN connectivity (PowerShell):**

*This is a generic Azure AD client-credentials check, not a UiPath-published script — use it as a
starting point for connectivity troubleshooting, not as an official UiPath procedure.*
```powershell
$tenantId = "<azure-tenant-id>"
$clientId = "<app-registration-client-id>"
$clientSecret = "<client-secret>"
$vaultName = "<key-vault-name>"

$tokenResponse = Invoke-WebRequest -Method Post `
  -Uri "https://login.microsoftonline.com/$tenantId/oauth2/token" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body "grant_type=client_credentials&client_id=$clientId&client_secret=$clientSecret&resource=https://vault.azure.net"

$token = ($tokenResponse.Content | ConvertFrom-Json).access_token
Write-Host "Token obtained: $($token.Substring(0,20))..."

# Test listing secrets
$secrets = Invoke-WebRequest -Method Get `
  -Uri "https://$vaultName.vault.azure.net/secrets?api-version=7.3" `
  -Headers @{ "Authorization" = "Bearer $token" }
Write-Host "Secrets accessible: $(($secrets.Content | ConvertFrom-Json).value.Count)"
```

---

### Option 2 — CyberArk CCP (Credential Provider)

**Architecture:**
```
Robot → Orchestrator → CyberArk CCP REST API (AIMWebService) → CyberArk Vault
```

**Prerequisites (confirmed):**
- Network connectivity between the Orchestrator service and the CyberArk CCP server
- CyberArk Central Credential Provider installed on a machine that allows HTTP connections
- CyberArk Enterprise Password Vault
- An Orchestrator "application" created in CyberArk PVWA (Applications tab → Add Application),
  authenticated via client certificate (2048-bit minimum)
- A Safe created in PVWA with the Orchestrator application added as a Safe member with
  **View Safe Members**, **Retrieve accounts**, **List accounts** permissions

📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/integrating-credential-stores#cyberark-ccp-integration

**Orchestrator Setup (Automation Cloud) — actual field names:**
```
1. Orchestrator → Tenant → Credentials → Stores tab → Add credential store
2. Type: CyberArk CCP
3. Name: <descriptive name for this store>
4. App ID: <Application ID configured in CyberArk PVWA>
5. CyberArk Safe: <Safe name defined in PVWA>
6. CyberArk Folder: <folder within the Safe where credentials live>
7. Central Credential Provider URL: <address of your CCP server>
8. Web Service Name: (optional — defaults to AIMWebService if left blank)
9. Client Certificate / Client Certificate Password: (for mutual TLS auth)
10. Server Root Certificate: (only needed if CCP's AIMWebService uses a self-signed root CA)
11. Select Create
```
📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores#cyberark-ccp

**CyberArk Errors you may see (verified against CyberArk's Application Provider Messages reference):**

> The error *codes* below are real CyberArk Credential Provider messages. The original draft of this
> KB had paired them with the wrong causes — corrected here against CyberArk's own documentation.

| Error | Actual CyberArk-documented cause | Fix |
|---|---|---|
| `APPAP004E` — Password object in Safe/folder was not found | The requested password object doesn't exist in that Safe/folder, **or** the application/Credential Provider user lacks permission for that specific password | Confirm the object exists in the exact Safe + folder queried; verify the App ID's account has retrieve rights on it |
| `APPAP007E` — Connection to the backend/Vault has failed | Network/communication error or timeout reaching the Vault (e.g. `ITACM012S` timeout, `ITACM022S` unable to connect) | Check network/firewall path from Orchestrator/CCP to the CyberArk Vault; confirm the Vault and CCP service are reachable and up |
| `APPAP008E` — Problem using the application user in the Vault | The application user is disabled, expired, connecting from an unauthorized/suspended network area, outside its permitted time slice, or has the wrong User Type (must be `AIMAccount`) | Enable/un-expire the App ID, verify the Orchestrator server's IP is in an allowed network area, confirm User Type = AIMAccount |
| SSL certificate error | CyberArk CCP cert not trusted by Orchestrator | Import the CyberArk CCP (AIMWebService) certificate into the Orchestrator server's trust store, or configure the **Server Root Certificate** field if self-signed |
| Connection timeout | CyberArk CCP not reachable | Check firewall/network path from Orchestrator to the CCP server |

📖 https://docs.cyberark.com/credential-providers/latest/en/content/messages/application%20provider%20messages%20-%20general.htm

---

### Option 3 — HashiCorp Vault

**Prerequisites:**
- HashiCorp Vault server accessible from Orchestrator — API port (**8200** in a typical install) open
  through any firewall between Orchestrator and the Vault server
- A configured secrets engine (see options below)
- An authentication method configured for Orchestrator to use

**Orchestrator Setup — actual field names:**
```
1. Orchestrator → Tenant → Credentials → Stores tab → Add credential store
2. Type: HashiCorp Vault (read-write) OR HashiCorp Vault (read-only)
3. Name: <descriptive name>
4. Vault Uri: https://<vault-server>:8200  (address of Vault's HTTP API)
5. Authentication Type — pick one:
   - AppRole (recommended) → Role Id + Secret Id
   - UsernamePassword → Username + Password
   - Ldap → Username + Password (+ optional "Use Dynamic Credentials" toggle)
   - Token → Token
6. Secrets Engine: KeyValueV1, KeyValueV2, ActiveDirectory, OpenLDAP, or LDAP
   (ActiveDirectory/OpenLDAP available only for the read-only store)
7. Secrets Engine Mount Path (defaults to kv / kv-v2 / ad depending on engine)
8. Data Path: path prefix used for all stored secrets
9. Authentication Mount Path: optional, only if you mounted auth on a custom path
10. Namespace: optional, HashiCorp Vault Enterprise only
11. Select Create
```
📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/integrating-credential-stores#hashicorp-vault-integration
📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores#hashicorp-vault

---

### Option 4 — BeyondTrust Password Safe

> **Important — corrected:** the BeyondTrust integration is **read-only**. Orchestrator can retrieve
> credentials from BeyondTrust but cannot create, update, or delete them there. There is no single
> generic "BeyondTrust" store type, API URL, or API Key field as previously drafted — the real
> configuration uses two distinct plugin types with their own fields.

**Orchestrator Setup — actual field names:**
```
1. Orchestrator → Tenant → Credentials → Stores tab → Add credential store
2. Type: BeyondTrust Password Safe - Managed Accounts
     OR: BeyondTrust Password Safe - Team Passwords
3. Name: <descriptive name>
4. BeyondTrust Host URL: <URL of your BeyondTrust Password Safe instance>
5. API Registration Key: <API registration key generated in BeyondTrust>
6. API Run As Username: <BeyondTrust username the API calls execute as>

If Managed Accounts:
7. Default Managed System Name: optional fallback if the asset's External Name has no System Name prefix
8. System-Account Delimiter: delimiter splitting System Name from Account Name
9. Managed Account Type: "system" (local accounts) or "domainlinked" (domain accounts)

If Team Passwords:
7. Folder Path Prefix: optional, prepended to all Orchestrator asset values
8. Folder/Account Delimiter: splits Path from Title in the Orchestrator asset

10. Select Create
```
📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/integrating-credential-stores#beyondtrust-integration
📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores#beyondtrust

---

## Using Credential Store Assets

Once a credential store is configured:

```
Orchestrator → Folder → Assets → Add Asset
Type: Credential
Credential Store: [select your configured store]
External Name: <identifier of the secret in the vault>
```

> **Important:** The External Name is used to locate the secret in the vault (often concatenated with
> a configured data path). Treat it as needing an **exact match** to what's provisioned in the vault.
> The previous claim that this is "case-sensitive for Azure Key Vault, case-insensitive for CyberArk"
> could not be verified against current UiPath documentation and has been removed — case-sensitivity
> behavior depends on the specific vault/secrets engine and should be confirmed for your store type
> rather than assumed. 📖 https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores

In Robot process (Studio):
```
Get Asset activity → Asset Name: "MyCredentialAsset"
→ Returns username + password from the vault at runtime
→ Credentials are never cached locally on the Robot machine
```

---

## Dedicated Automation Cloud (Private Cloud) — Migration Notes

> **Correction:** the original draft's specific DNS-zone and sequencing steps for this section could
> not be verified against UiPath documentation and have been replaced with verified, general guidance.
> Also note that **Automation Cloud Private Link** (connecting to the standard multi-tenant Automation
> Cloud over Azure Private Link, Enterprise plan, with primary/secondary gateways in West Europe /
> North Europe) and **Automation Cloud Dedicated** (a separate, single-tenant dedicated deployment) are
> two different offerings — don't treat them as the same migration path.

For customers migrating to **Automation Cloud Dedicated** (dedicated/private instance):

- [ ] Engage the UiPath Cloud team early — dedicated instance provisioning and any private
      connectivity option is coordinated with UiPath, not self-service
- [ ] If using Azure Private Link connectivity, work with UiPath to provision the private endpoint(s)
      on the UiPath side and confirm the approval/connection steps currently documented — do not rely
      on a fixed DNS-zone name without confirming it against current docs
- [ ] Multi-tenant → Dedicated migration: data migration is performed by the UiPath Cloud team
      (submit a Support Request / SR)
- [ ] Robot agents may require updated connection strings/endpoints post-migration — validate
      end-to-end connectivity after cutover before decommissioning the old tenant

📖 https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/introduction (the standalone Dedicated overview page has been merged into this general "About Automation Cloud" page, which now covers Cloud / Public Sector / Dedicated together — re-confirm Dedicated-specific details here going forward)

**General sequencing guidance (verify exact steps live with UiPath before executing):**
```
1. Customer/UiPath jointly scope the private connectivity requirement (Private Link vs Dedicated)
2. Customer provisions any required Azure-side resources (e.g., Private Endpoint) per current
   UiPath guidance for the chosen option
3. UiPath approves/completes the connection on their side
4. Customer validates DNS resolution and connectivity end-to-end per the current UiPath instructions
5. Update Robot connections/endpoints as instructed and re-test job execution
```

---

## Troubleshooting Credential Store Issues

```powershell
# Quick diagnostic: test credential retrieval from Robot machine
# Run in Studio → Debug mode with Get Asset activity
# Check Robot logs for credential fetch errors:
Get-Content "$env:LOCALAPPDATA\UiPath\Logs\*" | Select-String "credential|asset|vault|CyberArk|KeyVault" | Select-Object -Last 50
```

**Common cross-credential-store errors:**

| Error | Likely Cause |
|---|---|
| `Credential store connection failed` | Network/firewall blocking Orchestrator → Vault |
| `Invalid credentials` | Client Secret expired (AKV) or token/AppRole credentials expired (HashiCorp Vault) |
| `External name not found` | Secret name/path mismatch — check exact spelling and any configured Data Path prefix |
| `Permission denied` | SPN/App lacks `Set` (Key Vault Secrets Officer) permission for read-write mode, or CyberArk Safe access is missing |
| Works in Read-Only, fails in Read-Write | SPN only has the **Key Vault Secrets User** role — needs **Key Vault Secrets Officer** for a read-write store |

---

## Reference Links

- Azure Key Vault integration (prerequisites/setup): https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/integrating-credential-stores#azure-key-vault-integration
- Azure Key Vault store fields (Orchestrator UI): https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores#azure-key-vault
- CyberArk CCP integration (prerequisites/setup): https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/integrating-credential-stores#cyberark-ccp-integration
- CyberArk CCP store fields (Orchestrator UI): https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores#cyberark-ccp
- CyberArk Application Provider error messages (source of truth for APPAP*** codes): https://docs.cyberark.com/credential-providers/latest/en/content/messages/application%20provider%20messages%20-%20general.htm
- HashiCorp Vault integration: https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/integrating-credential-stores#hashicorp-vault-integration
- HashiCorp Vault store fields (Orchestrator UI): https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores#hashicorp-vault
- BeyondTrust integration: https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/integrating-credential-stores#beyondtrust-integration
- BeyondTrust store fields (Orchestrator UI): https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores#beyondtrust
- Multi-tenancy — About tenants: https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/about-tenants
- Multi-tenancy — Managing/creating tenants: https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/managing-tenants
- Allocating licenses to tenants: https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/allocating-licenses-to-tenants
- Automation Cloud Dedicated overview (merged into the general About page): https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/introduction
