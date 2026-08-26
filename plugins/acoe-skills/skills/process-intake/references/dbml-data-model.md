# Drafting the target data model in DBML

## When to produce one

Add a data model when the intake ends in **stored data** — a report that should become a
table, a register that should become a database, a process where the missing capability is
historisation. Roughly: if anyone in the recording says "we'd like to see it retrospectively",
"we copy last month again", "we need the history", or "it should go to Power BI", the model
is part of the answer.

Do **not** produce one for a pure task-automation intake (routing an approval, filling a form,
clicking through a GUI) where nothing new is persisted. An unnecessary schema invites a design
argument that delays the actual automation.

## Why DBML

It is readable in a pull request, it pastes straight into <https://dbdiagram.io> to give
stakeholders an interactive diagram, and it converts to real DDL for whichever database the
CoE picks (Azure SQL, SQL Server, PostgreSQL). You are proposing a shape, not committing to a
platform, and DBML expresses exactly that.

## How

Write `<slug>_model.dbml`, then:

```bash
python scripts/build_dbml_diagram.py work/<slug>_model.dbml            # -> .dot + .svg
python scripts/build_dbml_diagram.py work/<slug>_model.dbml --check    # parse/validate only
python scripts/build_dbml_diagram.py work/<slug>_model.dbml --sql postgres
```

The script parses DBML in pure Python (no install needed), warns about missing primary keys,
unknown table references and orphan tables, renders an ER diagram in CETIN brand colours via
Graphviz if `dot` is present, and emits DDL via `@dbml/cli` if that is installed. Ship the
`.dbml` **and** the rendered `.svg`: the file is the artefact engineers work from, the picture
is what gets discussed.

One DBML syntax trap the pure-Python parser tolerates but `dbml2sql` and dbdiagram.io do not:
enum values must be **one per line**, not `Enum s { a b c }`.

## Modelling guidance for intake work

**Model the grain the process actually produces.** If the manual output is one row per vehicle
per month with a variable set of cost columns, the table is one row per vehicle per cost
element per period — long, not wide. Reproducing the wide sheet in the database bakes today's
Excel limitations into tomorrow's warehouse, and the column set changes monthly anyway.

**Historise what changes underneath.** The single most requested capability in these intakes
is "who owned/drove/approved this, when". Model the master-data tables as slowly-changing
(`valid_from`, `valid_to`), snapshot at the same cadence the process runs, and say plainly in
the analysis that history cannot be backfilled — every month of delay is permanently lost
context. That framing is usually what gets the project prioritised.

**Keep a staging layer for external files.** Supplier spreadsheets arrive with no join key,
inconsistent formats, and corrections that land months later. A `stg_` table holding the file
as received, with the source filename and load timestamp, is what lets you reprocess when a
lessor reissues three months of invoices — and it is where reconciliation disputes get settled.

**Record the source system on every fact row.** Where the intake found a value arriving by two
paths (an ERP feed and a manual spreadsheet), a `source_system` column is what makes the
double-count visible instead of silent. If your analysis identified such a trap, the model is
where you fix it.

**Carry the semantic into a column name.** If the report means "posted in the period" rather
than "belongs to the period", call the column `posting_period`, not `period`. The definition
that gets lost in prose survives in a column name.

## Sketch to adapt

```dbml
Project <slug> {
  database_type: 'PostgreSQL'
  Note: 'Target model for <process>. Grain: one row per <entity> per <cost element> per period.'
}

Table dim_<entity> {
  <entity>_key   integer  [pk, increment]
  natural_key    varchar(32) [not null, note: 'source key, e.g. registration plate']
  attribute_a    varchar(64)
  valid_from     date [not null]
  valid_to       date
  Note: 'SCD2 — snapshotted at each close; history is not backfillable'
  indexes { (natural_key, valid_from) [unique] }
}

Table fact_<measure> {
  fact_id        bigint [pk, increment]
  <entity>_key   integer [not null, ref: > dim_<entity>.<entity>_key]
  posting_period date    [not null, note: 'period POSTED, not period the cost belongs to']
  amount         numeric(15,2) [not null]
  source_system  varchar(20)   [not null, note: 'guards against the double-count']
}

Table stg_<external_input> {
  row_id         bigint [pk, increment]
  source_file    varchar(255) [not null]
  loaded_at      timestamp    [not null]
  natural_key    varchar(32)
  amount         numeric(15,2)
}
```
