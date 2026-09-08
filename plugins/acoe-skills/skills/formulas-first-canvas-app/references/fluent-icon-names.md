# Fluent icon names that actually render

`Button.Icon` / `ModernButton.Icon` silently render an EMPTY CIRCLE for an
unknown icon name. There is no compile error and no app-checker finding, so a
wrong name survives every gate this skill has and only shows up in a
screenshot.

Two names that look obvious and do NOT work, both found live on 2026-09-08:

| Wrong | Symptom | Use instead |
|---|---|---|
| `List` | empty circle where the header's menu toggle should be | `GridDots` (the waffle the reference app uses) |
| `ArrowTrending` | empty circle on a dashboard navigation tile | `ArrowSync` |
| `Table` | empty circle — tried as the replacement above and ALSO failed | `ArrowSync` |

## The proven set

**Two contexts, two levels of evidence — do not conflate them.** The
reference app writes icon names in two places: as a direct control property
(`Icon: ="Add"`) and as a value inside a registry record (`Icon: "Table",`).
Only the first proves the name works as a **Button icon**. `Table` came from a
record literal, was used here as a Button icon, and rendered an empty circle —
so the list below is split accordingly.

## Proven as a Button `Icon` property

Every name below appears as `Icon: ="Name"` on a control in the Regional
Procurement Plan app, which is published and rendering:

```
Add        ArrowClockwise  ArrowDown   ArrowExit   ArrowLeft   ArrowReset
ArrowSync  ArrowUndo       ArrowUp     Checkmark   CheckmarkCircle
ChevronDown ChevronLeft    ChevronRight CircleFill Delete      Dismiss
Edit       Eye             Filter      GridDots    Home        Info
LockClosed Message         Open
```

Also verified live in this app's own dashboard tiles: `AppsListDetail`,
`Clock`.

## Registry-record values only — NOT verified as Button icons

`AppsList`, `ArrowSync`, `Checkmark`, `ClockAlarm`, `Home`, `Link`, `People`,
`Table`, `Warning`. `Table` is the proof this distinction matters.

Prefer a name from this list. If you need one that is not here, verify it by
looking at a rendered screenshot — a clean `compile_canvas` proves nothing
about icon names.

A `model.yaml` entity's `icon:` feeds a dashboard tile's `Icon`, so the same
rule applies there.
