# The component library

Eight components in `components/`. Copy the files you need into
`Src/Components/`, paste the tokens, and the screen templates work as written.

**These have not been compiled.** They were ported from a production app, but
the strict Power Fx engine has not seen them in this form. Treat first
compile as a debugging session, not a formality — and see "What was changed"
below for exactly where they differ from the tested originals.

## What each one is for

| Component | Job | Key inputs | Raises |
|---|---|---|---|
| `cmp_Header` | App chrome: back / menu, title, utility actions, loading bar | `DisplayName`, `AllowBack`, `AllowNavigation`, `IsLoading`, `NotificationCount`, `CanRefresh` | `OnBack`, `OnNavigate`, `OnSelectRefresh`, `OnSelectNotifications`, `OnSelectHelp` |
| `cmp_Navigation` | Icon rail / expanded menu, driven by the screen registry | `Screens` (default `constScreens`), `Navigation`, `AllowBack` | `OnClose`, `OnBack` |
| `cmp_CommandBar` | Row of round action buttons, each independently gated | `CanAdd`, `CanEdit`, `CanDelete`, `CanConfirm`, `CanShare`, `CanRemoveFilters`, `CanCustom` | one `On*` per verb |
| `cmp_FilterButton` | Column header that is also the filter/sort affordance | `Field`, `Label`, `Title`, `DataType`, `Choices`, `IsFiltered`, `IsSorted` | `OnSelect`; outputs `Value` (metadata record) |
| `cmp_Notification` | Toast stack with countdown | `Notifications`, `Duration` | `OnCancel(ThisRecord)` |
| `cmp_Dialog` | Modal confirm, optional date field | `Title`, `Description`, `SubmitLabel`, `CancelLabel`, `ShowDatePicker` | `OnSubmit`, `OnCancel`; outputs `DateOutput` |
| `cmp_Empty` | Empty-state row for a gallery | `Icon`, `Message` | — |
| `cmp_Spinner` | Full-screen blocking overlay | — (bind `Visible`) | — |

Every one sets `AccessAppScope: true`, so all eight read `constStyle` and the
colour tokens directly. None carries a private literal.

## The contracts that matter

**`cmp_Navigation` reads the registry, not a hand-built menu.** It filters
`constScreens` to `Type = enumScreenType.List`. Adding a screen to the menu is a
row in that table. Form screens carry `Group = ""` and stay out, because you
reach them from a list.

**`cmp_Notification` has exactly one producer.** Screens call `funcNotify(...)`
(or `funcNotifySuccess` / `funcNotifyError`); they never write `colNotifications`.
The record shape is fixed in three places that must agree — `funcNotify`, the
`OnStart` seed, and the component's `Notifications` default. If
`SortByColumns("Priority", ...)` ever sorts by nothing, one of the three drifted;
`check_collection_columns.py` catches it.

**`cmp_FilterButton.Value` is a metadata record**, which is why a filter dialog
can be written once for all columns instead of once per column. It is also the
construct behind the whole-record resolution trap — read that section of
`references/powerfx-limits.md` before you build a collection whose *type* comes
from this output.

**`cmp_CommandBar`'s `Can*` inputs are visibility, not authorization.** Gate them
on the same expression that guards the function behind the button. A hidden
button is not a permission check.

## What was changed from the originals

Every difference, so you can diff against your own copy if you have one:

| Component | Change | Why |
|---|---|---|
| `cmp_Notification` | **Added `AccessAppScope: true`** | Without it `Set(glBoolNotificationStart, …)` created a *component-scoped* global disjoint from the app global of the same name. The component worked; every app-side write to that name was a dead store raising no error. This is the bug fix in the set. |
| `cmp_CommandBar` | Added `AccessAppScope: true`; tokenised literals; dropped `CanSelectJobs` / `Entity` / `IsDeactivating`; renamed `SecondaryColor` → `DestructiveColor` | The first two were domain leftovers; the rename says what the colour is *for*. |
| `cmp_Empty` | Added `AccessAppScope: true`; `App.Theme.Colors.Primary` → `constPrimaryColor`; `Size: =16` → the type scale | 16 is off the scale and the theme colour is outside the token layer's control. |
| `cmp_Header` | **Rewritten, not ported.** Interface preserved; body rebuilt | The original carried a country-scope switcher and an entity vocabulary from one app. Screens port unchanged; the domain does not come with it. |
| `cmp_Dialog` | Date picker now opt-in via `ShowDatePicker` (default `false`) | A generic dialog should not carry one screen's requirement. |
| `cmp_Navigation` | Removed dead commented blocks and a hardcoded Czech label; tokenised | — |
| `cmp_FilterButton` | Accessible label now announces filtered/sorted state | Colour and icon alone do not reach a screen reader. |
| All | `AccessibleLabel` and `TabIndex` on every interactive control | This is normally the largest single app-checker finding count, and it is mechanical. |

## Known wart

`cmp_Notification` repeats `First(SortByColumns(Notifications, …))` about a dozen
times. That breaks rule 1 of this skill and it is deliberate: the obvious fix is a
Record output property, which is the exact construct that caused a 247-error
type-cycle cascade in the app this came from. Given that these components are
uncompiled, the tested-but-repetitive form beat the untidy risk. Fix it once you
have a compile loop.

That trade-off is the general rule, not an excuse for this file: **prefer the
tested shape over the tidy one while you cannot verify, and write down which you
chose and why.**

## Not included

`cmp_Filter` — the 913-line filter/sort dialog these buttons open. It is the
richest piece of the original framework, and the one whose record output caused
the cascade above. Porting it needs a compile loop, so it is deliberately out of
this set. `cmp_FilterButton` still works without it: wire `OnSelect` to whatever
filter UI you have.

Also absent: domain editors (a notes thread, a weekly-progress editor). Those
were specific enough that porting them would have meant rewriting them.

## Verifying a port

```bash
# tokens already inlined in <Src>/App.pa.yaml (what new_app.py produces):
python3 scripts/check_references.py --src <Src>
python3 scripts/check_tokens.py --src <Src>

# tokens kept in a separate Power Fx fragment, not yet pasted:
python3 scripts/check_references.py --src <Src> --tokens-file templates/design-tokens.pa.yaml
```

The first catches a component referencing a token you have not pasted — which in
the studio binder shows up as dozens of unrelated "unknown name" errors on
screens, not as one error in the component.
