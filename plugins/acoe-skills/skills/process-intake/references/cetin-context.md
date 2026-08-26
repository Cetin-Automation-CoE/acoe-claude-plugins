# CETIN intake context: decoding Czech transcripts and SAP references

Read this while reconstructing the process, not before. It exists because the same
handful of problems recur in every CETIN automation intake and each one costs an hour to
rediscover.

---

## 1. Machine transcripts mangle transaction codes

Teams transcription renders SAP codes phonetically, in Czech, letter by letter. It will
never produce `KOB1`. It produces `kop 1`. Treat every transaction code in the transcript
as a phonetic puzzle, resolve it against what the speaker says the transaction *does*, and
mark the result `**(verify)**` unless a participant spelled it out explicitly.

Confirmed decodings from previous sessions:

| Heard in transcript | Actual code | What it does |
|---|---|---|
| "kop 1", "kob jedna" | `KOB1` | Orders: actual line items. The backbone of any order-costed report |
| "A 5 z", "E 5 z", "KE pět zet" | `KE5Z` | Profit centre: actual line items |
| "IH 0 8", "I H nula osm" | `IH08` | Display technical objects. **Keyed on registration plate**, which SAP labels *technické identifikační číslo* |
| "z 1 F I podtržítko … škody" | `Z1FI_…_SKODY` | Custom damages/claims report |
| "zdomet", "do met", "z domec" | `ZDOMET` | Mileage and consumption. Often built originally for environmental reporting |
| "do met 2", "zdomet dvě" | `ZDOMET2` | Improved variant; typically carries fuel price per litre |
| "y podtržítko … VB 2", "…sedum 1 2" | custom vehicle master list | Vehicle master data as at a chosen date |

Reliable tells:

- `podtržítko` = underscore. `z` at the end of a spelled code is usually the letter Z —
  speakers disambiguate with a name, e.g. *"z jako Zuzana"*.
- Czech reads digits singly: "nula osm" = 08, "5 z" = 5Z.
- A `Z`/`Y` prefix means a customer-specific report, so there is no public documentation
  and the code cannot be inferred — it must be confirmed with the speaker.
- When a participant repeats a code back for their notes ("KE 5 Z, that we have"), that
  repetition is your most reliable source. Search for these confirmations.

## 2. Numbers are unreliable in a specific, detectable way

The transcriber renders a confidently-spoken multi-digit number as one token (`14375`,
`8300`, `5000`) but a hesitant one as separated digits (`7 6`, `6 1000846`). **Separated
digits mean the speaker was hesitating, not that the number has that many digits.**
"těch 7 6 kusů" is almost certainly *"six or seven units"*, not 76.

So: if a figure appears as spaced digits, do not state it as fact. Give both readings,
mark `**(verify)**`, and sanity-check against magnitude — if every other tier of the same
list is in single digits, 76 is the wrong reading.

Also watch for a figure the speaker offers as *typical* being different from the one they
just read off the screen. Both are worth reporting; conflating them is not.

## 3. Names

Czech surnames get mangled and the same person can appear three ways in one transcript
(*kolářová* / *Mikolářová*; *vinduška* / *jednoduška*). Two different people can also look
like transcription variants of each other when they are not — check whether the contexts
overlap before merging them. If one name only ever appears around report design and
another only around invoice distribution, they are probably two people.

State a name at the confidence the source supports, and mark reconstructions
`**(verify)**`. Never pair two names into a single attribution ("via X and Y") unless the
speaker actually paired them.

## 4. Who is usually in the room

CETIN automation intakes tend to have four shapes of participant. Identifying them
changes how you read a turn:

- **The process owner** — does almost all the talking, demonstrates their screen. The
  transcript extractor's word-count summary identifies them instantly. Their asides are
  where the exceptions live.
- **The RPA / automation lead** — asks for transaction codes, notes what access is
  missing, drives toward file handover and a robot mailbox. Their questions mark the
  boundaries of what is technically in scope.
- **Controlling** — consumes the output. Watch for them saying they *don't* use part of
  it; that is scope you can delete for free.
- **BI / data** — asks about the target database, schema, historisation, Power BI.

The process owner and the consumers frequently want different things and the meeting ends
without resolving it. Record that as an open decision, not as agreement.

## 5. Recurring structural traps

Check for each of these explicitly; they have appeared in more than one intake.

- **Posted-in-period vs. belongs-to-period.** Order-costed reports contain what was posted
  in the period. Everyone downstream assumes it means costs *of* the period.
- **Double counting via two paths.** A value that reaches the output both from the ERP
  (e.g. IFRS 16 postings flowing from a leasing module) and from a spreadsheet the owner
  maintains from supplier billing. The two never reconcile exactly.
- **Company codes that cannot be posted to.** An acquired entity kept in the ERP for
  registration or payroll only. Costs get booked to the vehicle's or asset's *old* order,
  and master data is deliberately deformed to avoid duplicate keys. This looks like a data
  quality problem and is actually a deliberate workaround.
- **Fallback ladders on master data** — look up as at the 1st, then the last day, then
  today. Each rung exists because of a real failure and each has different semantics.
- **Values that arrive years late.** Closing settlements, excess-wear charges, credit
  notes. They land against cost centres and people who no longer exist, and the owner
  researches the correct attribution by hand. This is usually red, not amber: history that
  was never recorded cannot be reconstructed by a robot.
- **VAT.** Prices pulled from operational reports are frequently gross where the report
  needs net. Cheap to automate, easy to miss, wrong by 21%.
- **Row limits on ERP exports.** A default selection variant that truncates silently is a
  correctness bug waiting to happen; note the exact variant used.

## 6. Access is usually the schedule risk

The automation team will typically lack authorization for at least one custom `Z`/`Y`
report, and requests route through a technical account. Capture: which transactions are
missing, who requests them, and the expected date. Where a blocked source carries little
value, say so — an explicit descoping decision beats a silent multi-week delay.
