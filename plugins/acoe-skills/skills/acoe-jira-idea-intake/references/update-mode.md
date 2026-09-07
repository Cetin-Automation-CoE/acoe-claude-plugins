# Updating an existing Idea

Create mode and update mode share the writing rules and the field reference. They differ in one
respect that changes everything: **in update mode there is already data in Jira, and anything
you write destroys what was there.** Jira keeps a history, but nobody reads it, so treat every
overwrite as permanent.

## When this applies

- The user names an issue key (`ACOE-4618`) or pastes a Jira URL.
- The user says *doplň / aktualizuj / oprav / přepiš / dodělej*, *update*, *add to*, *fill in*.
- The user hands over material and refers to an Idea that already exists, even loosely
  ("k té ideji na směrování zpráv jsem dostal čísla od podatelny").

Two shapes of update, and they need different handling:

| Shape | Typical case | Handling |
|---|---|---|
| **Fill-in** | An almost empty Idea created earlier just to track work, now the user brings the transcript, the numbers, everything | Runs like a normal intake, except the few populated fields are protected |
| **Targeted edit** | "Change Effort to L", "requestor is actually Nováková", "add the penalty figure" | Touch only what was asked, show the current value first |

Both use the same procedure below. The difference is only how many fields are in play.

---

## Step U1 — Read the issue before anything else

One call, always first, before drafting a single word:

```
Atlassian Rovo:getJiraIssue
  cloudId: cetin.atlassian.net
  issueIdOrKey: ACOE-4618
  fields: ["*all"]
  responseContentFormat: markdown
```

Never draft from the user's new material alone and never assume a field is empty. An Idea that
looks bare in a screenshot may have a Business Case somebody wrote three months ago.

If the key does not exist or is not an Idea, say so and stop. Do not create a new Idea as a
substitute for one the user thinks already exists.

**Check Delivery Type (`customfield_11396`) in the response before going any further.** If it
is anything other than `New Functionalities`, stop. Do not edit a single field, do not draft
anything, and tell the user this skill only handles `New Functionalities` Ideas because the
business case is tracked only for those. An `Internal Operations`, `Support & Maintenance` or
`Ad-Hoc` Idea is edited directly in Jira.

If Delivery Type is empty on an old Idea, ask the user whether it is a `New Functionalities`
Idea rather than assuming it. If they confirm, set it as part of the update.

## Step U2 — Sort every field into three buckets

| Bucket | Meaning | Consequence |
|---|---|---|
| **Empty** | no value in Jira | fill it exactly as in create mode, normal questions, no extra ceremony |
| **Filled, unaffected** | has a value, the new material says nothing about it | leave it completely alone, do not resend it, do not "tidy" it |
| **Filled, affected** | has a value, and the new material or the user's request changes it | **destructive.** Show old against new and get explicit approval before writing |

The third bucket is the whole point of this mode. A field that already carries a number
somebody defended in a meeting does not get silently replaced because a transcript implies a
different one.

Never blank a populated field just because the new source does not mention it. Clearing a
field happens only when the user explicitly asks to clear it.

## Step U3 — Text fields are composed, not replaced

Description and Business Case Description are the fields users most often "update", and
replacing them wholesale is how work gets lost.

**Read the existing text as source material, on equal footing with whatever the user just
brought.** Then compose one new version that:

- keeps every fact from the existing text that the new material does not contradict, including
  facts the new material simply does not mention
- adds what is new
- restructures to the current template, so an old Description without a `## Shrnutí` block gets
  one, and old prose gets sorted into the standard sections
- corrects what is genuinely superseded, and says so in the presentation

**Contradictions are questions, not merges.** If the Idea says 750 messages a day and the new
transcript says 400, do not average them, do not pick the newer one, and do not write "400
(dříve uváděno 750)" on your own initiative. Show both and ask which holds.

If the existing text is empty, this is simply create mode for that field.

## Step U4 — Present old against new, then wait

Show a three-column table containing **only the rows that change**. Unchanged fields are noise
and hide the rows that matter.

```
**ACOE-4618 — návrh změn**

| Pole | V Jira nyní | Nová hodnota |
|---|---|---|
| Affected People | *(prázdné)* | 3 |
| Minutes per Run | 10 | 1,5 |
| Effort Estimation | XS (0-1 MD) | L (10-20 MD) |
```

Then, underneath:

- **Mark every destructive row.** Anything overwriting a non-empty value gets flagged
  explicitly, for example with a `⚠` on the row and one line under the table naming which
  fields will be overwritten. An empty-to-filled row is not destructive and needs no flag.
- **Show the long text fields in full**, both versions, current and proposed. A table cell
  cannot carry a Description. If the current version is long, show it in full anyway. The user
  is approving its deletion.
- **Say what you kept.** One line: which parts of the existing text survived into the new
  version. This is what makes a wholesale rewrite reviewable.
- **List the contradictions** you found between the existing Idea and the new material, as
  questions, with both values.
- **Say what you are not touching**, in one line, so the user knows the scope of the write.

Close with: approve / change something / cancel. **Nothing is written until the user approves.**
Approval of the table is approval of that table, so if the user changes anything in reply, show
the revised table again rather than writing straight away.

## Step U5 — Write

One call, only the approved fields:

```
Atlassian Rovo:editJiraIssue
  cloudId: cetin.atlassian.net
  issueIdOrKey: ACOE-4618
  contentFormat: markdown
  fields: { ... }
```

Everything from `references/fields.md` still applies, in particular:

- **Business Case (`customfield_10089`) still needs paragraphs-only ADF** (§6). `contentFormat`
  does not convert custom fields on edit any more than it does on create.
- **Never write the calculated fields** (§1). Saved FTEs, Net Benefit 3Y, ROI 3Y, Payback
  Months and Idea Priority recompute themselves from the inputs.
- **Do not resend fields you are not changing.** Sending an identical value is harmless to the
  data but it pollutes the issue history and makes a real change harder to find later.
- **To clear a field, pass explicit `null`.** Only ever on an explicit request to clear it.
- **Do not touch status.** See `references/fields.md` §7.
- **Team** is already set on an existing Idea. Leave it. Only set it if it is empty.
- **Delivery Type** is never changed. The skill refuses Ideas that are not
  `New Functionalities`, so there is never a reason to rewrite this field. The one exception is
  filling it in when it is empty and the user has confirmed the Idea is `New Functionalities`.
- **External ID** often arrives later than the Idea itself, so an empty one is the common case
  to fill. If it already holds a different reference, that is a destructive change and needs
  the usual old-against-new approval.
- **Priority Override** is never touched. If the backlog owner moved an Idea to `Raised` or
  `Expedited`, an update must not quietly return it to `Standard`.

Afterwards, report what changed and what failed. If a field is rejected, name it. Do not retry
silently with a different value.

---

## Scoring inputs deserve a second look

Changing Affected People, Monthly Runs per Person, Minutes per Run, Monthly Run Cost, Effort
Estimation or PR Potential **reranks the Idea in the backlog**. When an
update touches any of them and the old value was not empty:

- say so explicitly in the presentation, not just as a table row
- show the old and the new derived saving side by side, so the user sees the size of the move:
  `dříve 3 × 5 250 × 10 = 2 625 h/měsíc → nyní 3 × 5 250 × 1,5 = 394 h/měsíc`
- run the same consistency checks as in create mode, including the impossibility check

An Idea whose numbers move by an order of magnitude on an update is usually an Idea whose
original numbers were wrong. Worth saying out loud.

## Requestor and Department on an existing Idea

If both are already set, do not re-ask and do not re-fetch the option lists. That saves the
metadata call entirely, so a targeted edit is two calls: one read, one write.

Fetch them only when one is empty or the user wants it changed.
