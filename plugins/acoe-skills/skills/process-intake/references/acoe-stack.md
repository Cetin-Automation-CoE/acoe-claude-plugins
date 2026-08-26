# Automation CoE: who you are writing for, and what they can build with

## Where the CoE sits

The **Automation CoE** is one of three sub-functions of the **PMO**, alongside the
Transformation Office and the Project Management Office. The PMO is headed by
**Peter Kukura (IT Strategy & PMO Director)** and operates as a peer of the fifteen CETIN
a.s. departments — although its formal Entra reporting line runs up through
**Jason Christos King (CEO, CETIN International)** rather than through the CZ CEO. That
matters when you trace an approval chain: the CoE's own governance and the business
sponsor's governance are different ladders.

The CoE's remit is **RPA and Power Platform based process automation across the business**.

Platform ownership sits elsewhere: the **IT Platforms Tribe** (Business Owner
**Jan Štěpánovský, CIO**) owns Integration, DevOps, low-code platforms, **RPA & Power
Platform**, AI, DMS and test automation. So the CoE delivers automations on platforms IT
Platforms runs — build decisions that imply new platform components need that tribe, not
just the sponsor.

Two other tribes come up constantly in intakes:

- **Enterprise Systems (SAP)** — Business Owner **Jan Menclík (Finance Director)**. Any
  intake touching SAP transactions, ERP data, or SAP authorizations routes here.
- **DWH/BI** — Business Owner **Katarína Vániková (CCO)**. Any intake whose output is a
  report, a dataset, or a Power BI model routes here.

An intake that ends in "extract from SAP, land in a database, surface in Power BI" therefore
crosses **three** owners. Name them in the analysis; a demand that names its owners moves,
and one that doesn't sits.

## Available stack

Write recommendations against what the CoE can actually deliver. Proposing something outside
this list means proposing a platform decision, which is a different and much slower
conversation — so do it deliberately and say so.

| Layer | Available | Typical use in an intake |
|---|---|---|
| **RPA** | UiPath-style attended/unattended robots | Driving SAP GUI where no API exists — running a transaction, applying a variant, exporting. The default answer for legacy screens |
| **Power Platform** | Power Automate, Power Apps, Dataverse | Mailbox triggers, approvals, file pickup, forms replacing a spreadsheet, human-in-the-loop steps |
| **Azure** | Functions, Logic Apps, Data Factory, Blob/Data Lake, Key Vault | Scheduled orchestration, file landing zones, anything needing real error handling and retries |
| **Databases** | Azure SQL, SQL Server, PostgreSQL | The target model. Historised snapshots, staging, the audit trail |
| **BI** | Power BI (+ DWH) | The consumption layer. Usually already in place and already fed by a manual Excel |
| **Scripting** | PowerShell, Python, TypeScript | Transformations, parsing, file wrangling, glue, API clients |

## Choosing a target shape

Most intakes resolve to one of four patterns. Recommend by what the source actually offers,
not by preference.

1. **RPA-led extraction → database → Power BI.** The source is a GUI-only legacy system
   (classic SAP transactions with no API). The robot runs the transaction and drops a file;
   everything downstream is a data pipeline. This is the standard shape for reporting intakes.
2. **Power Automate ingestion → database.** The input arrives as e-mail attachments from an
   external party. A shared mailbox plus a flow beats a robot here — fewer moving parts, and
   the CoE does not own the sender's format.
3. **Azure Data Factory / Functions pipeline.** There is a real API or database source.
   Skip RPA entirely; an RPA licence spent on something with an API is waste.
4. **Power App replacing a spreadsheet.** The "process" is largely someone maintaining a
   register by hand. Automating around the spreadsheet preserves the fragility — replacing it
   removes a single point of failure and creates the audit trail nobody currently has.

Most real intakes are a **combination**: Power Automate catches the supplier e-mails, a robot
runs the GUI extraction, Azure orchestrates, the data lands in Azure SQL, Power BI reads it,
and one Power App replaces the personal register. Say which component covers which step of
your process map — that is what turns an analysis into a backlog item.

## Two recommendations that recur

**Prefer a shared mailbox to a personal one.** Intakes are full of files arriving in one
person's inbox. Getting a shared mailbox created is cheap, unblocks automation, and removes a
holiday-cover risk that exists today regardless of whether anything is automated.

**Land the data before shaping it.** Where today's process ends in an Excel that a consumer
copies month after month, recommend a database table as the first deliverable and generate the
legacy Excel layout from it during transition. It preserves the consumer's workbook, creates
the historisation everyone asks for, and decouples the two projects.

## Cost and licensing notes worth flagging

- Unattended RPA robots are licensed per robot and need a machine; a process that runs once a
  month competes for that capacity with daily ones. Say what the schedule is.
- Premium Power Automate connectors (including SQL, and custom connectors) need premium
  licensing. If a design depends on one, flag it — it is a real approval step.
- Anything touching SAP needs authorization on a technical/service account, requested through
  the SAP tribe. This is routinely the longest lead time in the whole project; put the
  expected date in the actions table.
