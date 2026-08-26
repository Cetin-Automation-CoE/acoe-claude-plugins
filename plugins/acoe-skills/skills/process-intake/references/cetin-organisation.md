# CETIN organisation: routing an intake to the right owners

Condensed from the CETIN Company Context file (compiled 30 July 2026, CETIN **Company
INTERNAL**). Use it to name the accountable people in the analysis. A demand that names its
business owner, its delivery tribe and its system owner moves; one that doesn't sits in a
backlog while somebody works out who to ask.

Names are B-1 level (department heads) only — tribe leads and product owners change too often
to record and are omitted deliberately.

## The company in one paragraph

CETIN a.s. is the Czech wholesale telecommunications infrastructure operator, spun off from
O2 in 2015, owned via CETIN Group N.V. by PPF Group. It builds and operates the network and
sells access to *all* retail operators on equal terms — it has no end consumers. ~3,000
employees, 99.6% population coverage. **Nová optika s.r.o.** (founded 2025) is the fibre
build-out subsidiary — worth knowing, because it shows up in finance processes as a separate
accounting entity that frequently cannot be posted to directly. CEO: **Tomáš Kouřil**.

## Departments most likely to own an intake

The CEO has 15 direct reports. The ones that appear in automation intakes:

| Department | Head | Why it shows up |
|---|---|---|
| **FTTH Build-out Program** | David Sýkora | Fibre rollout programme: programme management, **NGA coordination**, strategic planning, business analysis. Owns anything NGA/FTTH — including the NGA6 contract process |
| **Legal Affairs** | Ľubomír Bubelíny | Legal counsel, contract support, regulatory/compliance. Consulted on contract templates, powers of attorney, e-signature validity |
| **Finance** | Jan Menclík | Tax, controlling, billing/accounting, cash, procurement, **ERP**. Owns the SAP tribe. Most back-office intakes land here |
| **IT** | Jan Štěpánovský (CIO) | Enterprise applications, infrastructure, architecture. Owns IT Platforms (RPA & Power Platform), IT Office, Enterprise Architecture |
| **Commercial** | Katarína Vániková (CCO) | Sales, product, service delivery — and **BI/DWH** |
| **HR & Support Services** | Milena Synáčková | HR, payroll/HRIS, and **Transport & Support Services** — the fleet function |
| **Network & Services Operation** | Radek Myška | NOC, RAN ops, field maintenance; owns Digital Operations |
| **Fixed Network Planning & Deployment** | Pavel Michal | Network inventory/GIS, plan & build |
| **Security & IMS** | Pavel Rivola | Cyber, physical security, BCM. Consulted on anything touching credentials or data |
| **PMO** | Peter Kukura | Transformation Office, **Automation CoE**, Project Management Office |

## Tribes you will need to name

Tribes are the cross-functional delivery structure under the departments. Each has a Business
Owner who is the relevant department head.

| Tribe | Business Owner | Owns |
|---|---|---|
| **Enterprise Systems (SAP)** | Jan Menclík (Finance) | SAP — ERP, portals, BW, LMS |
| **IT Platforms** | Jan Štěpánovský (IT) | Integration, DevOps, low-code, **RPA & Power Platform**, AI, DMS, test automation |
| **DWH/BI** | Katarína Vániková (Commercial) | Data warehouse and BI |
| **Digital Operations** | Radek Myška | Service assurance / service delivery apps, monitoring, automation & innovation |
| **Network Inventory/GIS** | Pavel Michal | Inventory, GIS, construction portal, build workflow tooling (incl. Power Apps) |
| **IT Office** | Jan Štěpánovský | IT standards, IDM, CMDB, PAM, PKI, SIEM — i.e. **access requests** |
| **Enterprise Architecture** | Jan Štěpánovský | Architecture standards (governance, owns no systems) |

An NGA/fibre intake will usually name **FTTH Build-out Program** as business owner and
**Legal Affairs** for anything touching contract wording or signatures.

A typical reporting-automation intake crosses **SAP** (source and authorizations), **IT
Platforms** (the robot and the Power Platform components), **DWH/BI** (the target model and
Power BI) and **IT Office** (the technical account). Say so explicitly in the actions table —
four owners is normal, and discovering them one at a time is what makes these projects slow.

## Value chain, for placing the process

Main flow: **Bid Management → CRM → Service Ordering → Service Provisioning → Service
Assurance → Network Maintenance**, with a parallel financial branch **Service Provisioning →
Billing → Enterprise Resource Management**.

Supporting: Service Provisioning ↔ Network Construction; Service Provisioning ↔ Workforce
Management; Network Construction → Network Inventory; Network Monitoring → Network Operation.
Standalone layers: General/Governance, Technology Base.

Most back-office intakes (reporting, accruals, invoice handling, fleet) sit in the **ERM**
box at the end of the financial branch, not on the main value chain. That is worth stating —
it sets expectations about business criticality and about which governance applies.

## Handling this material

The context file is **Company INTERNAL**. Reproduce only what the deliverable needs: naming a
business owner and a tribe is the point; pasting the org chart into a document that will be
shared outside the team is not. Statements marked *(unconfirmed)* in the source are inferred
from job titles — carry that uncertainty through rather than stating them as fact.
