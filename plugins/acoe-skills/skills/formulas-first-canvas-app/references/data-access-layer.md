# The data-access layer

## The invariant

**A data-source name may appear as code in exactly one region of `App.Formulas`.**

Everywhere else — every screen, every component — reads flat scalar collections and
calls `funcLoadX` / `funcSaveX` / `funcDeleteX`. Screens never see a choice wrapper
(`{Value: …}`), a lookup record (`{Id: …, Value: …}`), a claims string, or a
per-entity physical table name.

Prose is exempt: a list name in a comment or a UI label is documentation, not coupling.
The guard script strips comments and quoted strings before matching, which is what makes
the invariant enforceable rather than aspirational.

## Why this specific boundary

Changing backends, adding a caching layer, or splitting one logical entity across
several physical tables becomes **an edit to ~20 function bodies** instead of a hunt
through ten thousand lines of screen YAML. That difference is the whole argument. It is
also the only architectural boundary in a canvas app that a twenty-line script can
verify completely, which is why it is the first structural rung of the refactor ladder.

## Shape

```
// ============================================================
// ===== DATA ACCESS LAYER — BEGIN ============================
// ============================================================

// --- scope -------------------------------------------------
constItemsInScope = Filter(colItems, …);   // one base for grid, filters, counters

// --- read --------------------------------------------------
funcLoadItems(): Void =
{
    ClearCollect(colItems,
        // MOCK — replace on switch day
        Table({ Key: "A|1", Title: "…", Status: "Planned", Amount: 0 })
    );
    // SWITCH DAY:
    // ClearCollect(colItems,
    //     ForAll(MyList As r, {
    //         Key:    r.Suffix & "|" & r.ID,
    //         Title:  r.Title,
    //         Status: r.Status.Value,          // choice unwrapped HERE
    //         Amount: r.Amount
    //     })
    // );
};

// --- write -------------------------------------------------
funcSaveItem(): Void =
{
    // reads the typed global glFormDraft — UDFs take record params unreliably
    …
};

// ============================================================
// ===== DATA ACCESS LAYER — END ==============================
// ============================================================
```

## Rules inside the region

1. **Translate on both edges.** Unwrap `{Value:}` / `{Id:,Value:}` / claims on the way
   in; re-wrap on the way out. Nothing outside the region knows those shapes exist.
2. **Flat scalars only** in the collections screens read. No nested records.
3. **Composite keys where physical ids are not globally unique.** If an entity lives in
   five per-country lists, SharePoint ids collide across them — `HU|1` and `BG|1` both
   exist. Compose `suffix & "|" & id` as Text and key everything on it. Decide this at
   the start; retrofitting a key type is expensive.
4. **Write path enforces authorization**, once, here. Not per screen — a screen-level
   check is one screen away from being forgotten.
5. **One loading indicator.** `funcStartLoading()` / `funcStopLoading()` around every
   operation, so the spinner cannot desync from reality.

## Mock-first development

You can build the entire app against seeded collections before the backend exists, and
you should — it is faster and it forces the boundary to be real.

**But Power Fx cannot compile a reference to a data source that does not exist yet.**
So there can be no `constUseBackend` flag: the switch cannot be a runtime toggle. It is
a source edit.

Consequences to plan for, not discover:

- The real backend bodies sit **commented** beneath each mock, marked consistently
  (`// SWITCH DAY:`) so they are greppable.
- Those bodies have **never been compiled**. Treat switch day as a debugging session,
  not a flip. Budget accordingly and say so out loud when someone asks "is it ready".
- Get units and directions right in the mock seeds. A mock that stores a converted value
  where the real column stores the native one will silently double-convert on switch
  day, and the bug will look like a backend problem.

## Switch-day procedure

1. Provision the backend.
2. Add the data sources in Power Apps Studio (the app must know them before any formula
   referencing them can compile).
3. In each `funcLoadX`: delete the mock seed, uncomment the body beneath it.
4. In each `funcSaveX`: same, plus re-wrap choice fields.
5. Replace any hardcoded identity/context defaults with the real resolution.
6. Run all four guard scripts, then compile, then fix the cascade.

## Guard

```bash
python3 scripts/check_data_layer.py --src <Src> --datasource-pattern 'PP_[A-Za-z]'
```

Checks four things: no data-source name as code outside the region; both banners
present (without them the region test passes vacuously — the failure mode that makes a
guard worse than none); no direct writes to data collections outside the region; and
app-state collections (`colFilters`, `colSorts`, `colBack`, `colNotifications`) exempted
from that last rule, since screens legitimately own those.
