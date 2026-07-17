# Standalone Orchestrator — Fresh Install Guide

## Scope
New installation of UiPath Orchestrator (Standalone Server) on a Windows Server VM.
Covers single-node and multi-node (HA) deployments.

---

## Pre-flight Checklist

Before starting the installation, confirm ALL of the following:

| Check | Requirement |
|---|---|
| OS | Windows Server 2016 / 2019 / 2022 (64-bit) 📖 [Software Requirements](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-software-requirements) |
| RAM / CPU / Disk | Sizing varies significantly by deployment size — do not rely on a single flat minimum. Dev/small production (<20 robots) starts around 4 CPU cores / 4 GB RAM / 100–150 GB disk for the web app server; large multi-node deployments need 16+ cores / 32+ GB RAM / SSD storage. Size per the official tables for your robot count. 📖 [Hardware Requirements](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-hardware-requirements) |
| .NET / ASP.NET Core | ASP.NET Core Hosting Bundle 6.0.x or 8.0.x. Only the Core module is required (no runtime) — install with `OPT_NO_RUNTIME=1` unless Test Manager is also needed. 📖 [Software Requirements](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-software-requirements) |
| IIS | IIS 10+ with URL Rewrite 2.1+ module; required role services enabled (see Phase 1) 📖 [Software Requirements](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-software-requirements) |
| SQL Server | SQL Server 2014 / 2016 / 2017 / 2019 / 2022 (Standard or Enterprise), or Azure SQL Database / Amazon RDS for SQL Server / Google Cloud SQL for SQL Server 📖 [Software Requirements](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-software-requirements) |
| SQL Account | `dbcreator` server role, granted **before** installing, if Orchestrator is to create the database. If that's restricted, pre-create an empty database and grant `db_owner` (or the granular `db_datareader` + `db_datawriter` + `db_ddladmin` + `EXECUTE ON SCHEMA::dbo`) instead. `sysadmin` is **not** a documented requirement. 📖 [Prerequisites for Installation](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-prerequisites-for-installation) |
| SSL Certificate | Valid certificate for the Orchestrator FQDN (not self-signed for prod). Identity Server's signing certificate additionally needs a ≥2048-bit key, a private key accessible by the AppPool user, and must not be expired. 📖 [Prerequisites for Installation](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-prerequisites-for-installation) |
| Firewall | Port 443 open inbound (Users/Robots ↔ Orchestrator); 1433 open to SQL Server. (9200/9300 for Elasticsearch, 5601 for Kibana, if used.) 📖 [Hardware Requirements — TCP Ports](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-hardware-requirements) |
| Admin rights | Local Administrator on the install server; the account running the installer must also be a **Domain User**. 📖 [Prerequisites for Installation](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-prerequisites-for-installation) |
| License | Valid `.license` file or online activation key ready |

---

## Step-by-Step Install Checklist

### Phase 1 — Prepare the Server

- [ ] **1.1** Install IIS with the following role services. This is exactly the list UiPath's own `InstallRolesAndFeatures.ps1` script installs:
  ```
  Web Server → Common HTTP Features: Default Document, HTTP Errors, Static Content
  Web Server → Security: Request Filtering, URL Authorization, Windows Authentication
  Web Server → Application Development: ASP.NET 4.5, .NET Extensibility 4.5, Application Initialization,
                                         ISAPI Extensions, ISAPI Filters, WebSockets
                                         (Windows Server 2019 ships with ASP.NET 4.7 / .NET Extensibility 4.7
                                          by default — that satisfies the requirement)
  Management Tools: IIS Management Console
  Features (outside the Web Server role): Client for NFS
  ```
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/server-roles-and-features

  Rather than hand-typing an `Install-WindowsFeature` command, use UiPath's bundled script, which installs exactly the roles/features above automatically (referenced directly from the official prerequisites page):
  ```
  https://raw.githubusercontent.com/UiPath/Infrastructure/master/Setup/InstallRolesAndFeatures.ps1
  ```
  Run `IISRESET` after installing.
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-prerequisites-for-installation

- [ ] **1.2** Install the ASP.NET Core Hosting Bundle (download from Microsoft):
  ```
  https://dotnet.microsoft.com/en-us/download/dotnet/6.0  (ASP.NET Core Module 6.0.x)
  https://dotnet.microsoft.com/en-us/download/dotnet/8.0  (ASP.NET Core Module 8.0.x)
  ```
  Only the Core module needs to be installed — run the Hosting Bundle installer from an elevated command line with `OPT_NO_RUNTIME=1` (omit this flag only if you also plan to install Test Manager). Run `IISRESET` after installing.
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-software-requirements

- [ ] **1.3** Import SSL certificate into the Windows Certificate Store:
  ```
  certlm.msc → Personal → Certificates → Import (.pfx file)
  Note the thumbprint or Subject — needed later
  ```
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/certificate-considerations

- [ ] **1.4** Prepare SQL Server:
  - Create a dedicated SQL login for Orchestrator (SQL Auth or Windows Auth); make sure its **Default Language is set to English** — otherwise the site fails to start with a "conversion of a varchar data type to a datetime data type" error.
  - Grant the `dbcreator` server role **before** installing if you want the installer to create the database. If policy doesn't allow `dbcreator`, pre-create the empty database yourself and grant the login `db_owner` (or the granular `db_datareader` + `db_datawriter` + `db_ddladmin` + `EXECUTE ON SCHEMA::dbo`) — `db_ddladmin` is only needed for install/upgrade and can be revoked afterward.
  - Confirm collation is `Latin1_General_CI_AS`; `READ_COMMITTED_SNAPSHOT` is set automatically for a newly created database.
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-prerequisites-for-installation

### Phase 2 — Run the Installer

- [ ] **2.1** Download the correct Orchestrator MSI (`UiPathOrchestrator.msi`) from the UiPath Customer Portal
- [ ] **2.2** Right-click MSI → Run as Administrator
- [ ] **2.3** Accept the license agreement
- [ ] **2.4** On the **Product Features** step, choose whether to also install the optional **Insights** and/or **Test Automation** features.
  Note: Orchestrator, Identity Server, Webhooks, and the Resource Catalog Service are **not** separately selectable checkboxes — all four are always installed together as the base product's "included services." Only Insights and Test Automation are optional add-ons.
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-the-windows-installer
- [ ] **2.5** On the **Orchestrator Database Settings** step, configure:
  - SQL Server Host: `<server>\<instance>` (default `.` for localhost) or `<server>,<port>` for a custom port
  - Database Name: default `UiPath` (some special characters and names over 123 characters are not supported)
  - Authentication mode: Windows Integrated Authentication (default) or SQL Server Authentication
  - Clicking **Next** triggers the installer to validate the SQL connection automatically; a dialog appears if it fails
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-the-windows-installer
- [ ] **2.6** On the **Orchestrator IIS Settings** step, configure:
  - Website name: fixed to `UiPath Orchestrator` (not editable)
  - Website Port: default `443` (HTTPS)
  - Add firewall rules for this port: optional checkbox to auto-add the rule
  - SSL certificate: Subject or Thumbprint of the certificate to secure the site
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-the-windows-installer
- [ ] **2.7** On the **Identity Server Settings** step, set the **Orchestrator Public URL** — the FQDN users/robots will use, e.g. `https://orchestrator.company.com`. Defaults to `https://<hostname>` (or `https://<hostname>:<port>` for a non-443 port).
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-the-windows-installer
- [ ] **2.8** Click **Install** on the **Ready to install** step. Orchestrator installs to `C:\Program Files (x86)\UiPath\Orchestrator` by default — the install path cannot be changed after the fact. No fixed install duration is documented; it varies with server specs.
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-the-windows-installer
- [ ] **2.9** In IIS Manager, select the Orchestrator server node → **Feature Delegation** → right-click **Authentication - Windows** → set to **Read/Write**. Then start the website.
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-the-windows-installer

### Phase 3 — Post-Install Configuration

- [ ] **3.1** Verify IIS Application Pools are running:
  ```
  IIS Manager → Application Pools
  → UiPath Orchestrator (Running) — this app pool name is fixed by the installer
  → Identity Server, Webhooks, and Resource Catalog each get their own app pool — verify all are Started
  ```
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-the-windows-installer

- [ ] **3.2** Verify the Identity Server signing certificate meets requirements (≥2048-bit key, private key accessible by the AppPool user, not expired) and that its thumbprint is set correctly:
  ```
  C:\Program Files (x86)\UiPath\Orchestrator\Identity\appsettings.Production.json
  → "SigningCredential" section
  ```
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-is-appsettings-json
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-prerequisites-for-installation

- [ ] **3.3** Run the Platform Configuration Tool to validate setup:
  ```powershell
  cd "C:\Program Files (x86)\UiPath\Orchestrator\Tools\PlatformConfiguration"
  .\Platform.Configuration.Tool.ps1 -Readiness -SiteName "UiPath Orchestrator"
  ```
  If PowerShell blocks the script as unsigned, run `Set-ExecutionPolicy -ExecutionPolicy Unrestricted` (permanent) or `powershell.exe Set-ExecutionPolicy Bypass` (single session) first.
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/platform-configuration-tool

- [ ] **3.4** Access Orchestrator in browser: `https://<your-fqdn>`
  - Host admin credentials are set during the **Orchestrator Authentication Settings** install step (Host password / Confirm password). Log in with Tenant Name `host`.
  - Create first Tenant
  - Activate license
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-the-windows-installer

- [ ] **3.5** Check Windows Event Viewer for errors:
  ```
  Windows Logs → Application
  Look for Level=Error, Source=.NET Runtime, followed by Source=IIS AspNetCore Module V2 entries
  — this pattern indicates an ASP.NET Core startup failure (HTTP 500.30)
  ```
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/troubleshooting-http-error-50030-aspnet-core-app-failed-to-start

---

## Validation Checklist

- [ ] Orchestrator portal loads without errors
- [ ] Host admin login works
- [ ] Tenant creation succeeds
- [ ] License activated and seat counts correct
- [ ] Robot can connect (test with UiPath Assistant → Machine Key)
- [ ] Event Viewer: no critical errors in Application log
- [ ] Identity Server health: `https://<fqdn>/identity/.well-known/openid-configuration` returns JSON (note: path is `/identity`, not `/identity_`)
  📖 https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-installation-troubleshooting

---

## Common Install Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| Database creation fails during install | SQL login lacks the `dbcreator` server role before install | Grant `dbcreator` at the server level before installing, or pre-create the DB and grant `db_owner` / the granular db-level roles instead 📖 [Prerequisites](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-prerequisites-for-installation) |
| "The Remote Certificate Is Invalid" | Certificate's public key not imported, or not placed in the Trusted Root Certification Authorities store of the local machine | Import the certificate's public key into Trusted Root CAs on the Orchestrator machine 📖 [Troubleshooting](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-installation-troubleshooting) |
| "Invalid Identity Access Token Authentication Options. Please Check Web.config" | Identity Server wasn't installed alongside Orchestrator (commonly seen with the Azure App Service install script) | Install Identity Server together with Orchestrator — Orchestrator does not work without it 📖 [Troubleshooting](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-installation-troubleshooting) |
| "Too Many Redirects" | Three documented causes: (1) Identity Server SSL cert doesn't match the Orchestrator/IS URL; (2) ASP.NET Core Hosting Bundle installed incorrectly — check `https://localhost/identity`, a `500.19 Error Code: 0x8007000d` means a missing/malformed web.config; (3) **Host name** (IIS Settings step) and **Orchestrator Public URL** (Identity Server Settings step) didn't match during install | Match the cert to the URL; reinstall the Hosting Bundle if 500.19 appears; if URLs already diverged, update `IdentityServer.Integration.Authority` in `UiPath.Orchestrator.dll.config` and the `[identity].[ClientRedirectUris]` table, then run `IISReset` 📖 [Troubleshooting](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-installation-troubleshooting) |
| HTTP Error 500.30 — "ASP.NET Core app failed to start" | ASP.NET Core Module couldn't start the .NET Core CLR in-process | Check Windows Event Viewer for `Level=Error`, `Source=.NET Runtime`, followed by `Source=IIS AspNetCore Module V2` entries, and the ASP.NET Core Module `stdout` log 📖 [500.30 Troubleshooting](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/troubleshooting-http-error-50030-aspnet-core-app-failed-to-start) |
| Resource Catalog app pool not created automatically (on upgrade) | Automatic app-pool provisioning for Resource Catalog failed | Re-run the installer from the command line with `APPPOOL_USER_NAME` / `APPPOOL_PASSWORD` specified 📖 [Troubleshooting](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-installation-troubleshooting) |
| Unable to connect to SQL Server | Wrong connection string, closed firewall port, or SQL not listening on a fixed port | Confirm port 1433 (or custom port) is open, TCP protocol is enabled in SQL Server Configuration Manager, and the service listens on a fixed (not dynamic) port; test connectivity with SSMS from the install server 📖 [Prerequisites](https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-prerequisites-for-installation) |

---

## Reference Links

- Hardware Requirements: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-hardware-requirements
- Software Requirements: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-software-requirements
- Prerequisites for Installation: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-prerequisites-for-installation
- Server Roles and Features: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/server-roles-and-features
- The Windows Installer: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-the-windows-installer
- Platform Configuration Tool: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/platform-configuration-tool
- Installation Troubleshooting: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/orchestrator-installation-troubleshooting
- HTTP 500.30 Troubleshooting: https://docs.uipath.com/orchestrator/standalone/2023.10/installation-guide/troubleshooting-http-error-50030-aspnet-core-app-failed-to-start
