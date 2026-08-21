# UI.md

Purpose: describe the Genre Writer frontend as it actually behaves today — its
states, what functionality is reachable from each, and what each column shows
top to bottom. This file is meant to be edited (annotate, correct, add `FIX:`
notes under any state or gap) and then handed to an MCP-driven UI agent as the
spec for what to change. Keep the structure intact (state template, column
template, checklist gaps) so an agent can diff future UI behavior against it.

Source of truth: `frontend/src/App.tsx` and the components it renders
(`IngestForm`, `PlotCarousel`, `HbarVisual`/`ActHbar`, `Subplots`,
`EncodingRules`, `TopicCardGrid`, `CardEditForm`, `Sidekick`, `StatusIcon`,
`IconButton`).

## Status (post mockup-driven refactor)

The two items iteration 9 left open — the topic carousel and AI-managed
encoding rules — were both explicitly commissioned and built in the
refactor described in "Iteration 10" below, working from a mockup
(`UI.png`) the author provided. That refactor replaced the previous
Notecards + click-a-segment-see-a-grid architecture entirely, so most of
the Column layout / States / Gaps sections after the progress log describe
the **current** app; the "Archived history" section preserves iterations
1-9's log for provenance but describes UI surfaces (`Notecards.tsx`,
`PlotViewer.tsx`, the old scoped-per-section `Sidekick`, the encoding-rule
add/edit form) that no longer exist.

Re-run `uv run pytest -q` (backend) and `npx tsc --noEmit` (frontend)
before making changes.

## Iteration 10 — mockup-driven refactor: Sidekick drives the app

Commissioned directly by the author with a mockup (`UI.png`, described
below) and explicit instructions, not a self-directed loop iteration.
Every part was actually built, not deferred:

- **Sidekick tool-calling (backend).** `app/sidekick/tools.py` defines 8
  bounded tool schemas — `set_topic_excluded`, `set_theme_excluded`,
  `promote_theme_to_subplot`, `remove_topic_from_theme`, `set_topic_act`,
  `add_encoding_rule`, `update_encoding_rule`, `delete_encoding_rule` —
  each mapped straight to an existing, already-tested repository function
  (no new mutation capability was introduced beyond what buttons already
  did). `app/sidekick/llm.py` now runs a real multi-round tool-call loop
  against litellm: call the model with `tools=`, execute any tool calls
  against the real database, feed results back, repeat up to 4 rounds.
  `POST /sidekick/ask` now returns `{answer, actions}` so the frontend
  knows whether to refetch. 17 backend tests cover every tool function
  individually (including unknown-tool and nonexistent-id error paths)
  and the full loop with a mocked `litellm.completion`.
- **Topic/Theme carousel (frontend), replacing Notecards and the old
  click-a-segment grid.** `PlotCarousel.tsx` is a Topic View / Theme View
  toggle (blue / orange, matching the mockup) with Previous/Current/Next
  navigation tiles showing real titles, and a big Editor box below with
  only Edit → Save/Cancel (`CardEditForm`, unchanged) — no Exclude,
  Promote, or act-reassignment buttons anywhere in it, since the mockup
  and the author's instructions moved those to the Sidekick. Theme View
  additionally shows the theme's topics as a grid of small icon tiles
  ("Topics icons" in the mockup); clicking one jumps to that topic in
  Topic View.
- **`ActHbar` split into `HbarVisual` (pure bar rendering: segments,
  tooltip, position marker) + `ActHbar` (adds the click-to-select-grid
  behavior on top).** This let the new carousel reuse the bar visual with
  its own click behavior (jump the shared "current topic" pointer to that
  act) while Subplots keeps using `ActHbar` exactly as before, unchanged.
  The main Plot Viewer bar and the carousel share one `currentTopicId`
  state lifted to `App.tsx`, so the bar's position marker always points at
  whatever topic the carousel is showing.
- **Icons instead of text for status.** `StatusIcon.tsx` (a small
  inline-SVG tag icon and eye-slash icon) replaced the plain "Excluded"
  text tag and the underlined theme-name link everywhere topics are shown
  — `TopicCardGrid` (still used by Subplots) and the new carousel both use
  it now.
- **Act-select dropdown removed** from `TopicCardGrid` entirely (and its
  now-dead CSS deleted) — redundant with the Hbar's own position marker,
  per the author's explicit instruction. Subplots never used it, so this
  was a pure subtraction with no follow-on changes needed there.
- **Encoding Rules is now display-only.** `EncodingRules.tsx` dropped the
  add/edit/delete form entirely; it renders each rule as a plain pill
  (matching the mockup). Managing rules now only happens through Sidekick,
  via the same tool-calling path as everything else.
- **Right column reordered** to Encoding Rules above Sidekick, matching
  the mockup (previously Sidekick was on top).
- **`Notecards.tsx` and `PlotViewer.tsx` deleted** — nothing imports them
  anymore; their functionality is now `PlotCarousel` + the top `HbarVisual`.

Explicit scoping decisions made along the way, disclosed rather than
silently assumed:

- **Subplots was left completely unchanged.** The author's instructions
  named "Plot Viewer, topics and themes in the center column" — Subplots
  wasn't named, has different (cross-document) scope from everything else
  in the center column, and still has real working Exclude/Remove buttons
  the Sidekick doesn't cover. Removing its buttons or folding it into the
  carousel would have been guessing past what was asked.
- **The mockup's stacked/nested small bars above the toggle (a tiny
  three-dot row plus two smaller indented bar groups) were not
  replicated pixel-for-pixel.** Read as illustrating "smaller bars for
  recursive/subplot structure" (already true — Subplots' own bar renders
  at `size="small"`), not as a literal always-visible-summary-of-every-
  subplot widget, since building that would need a new bulk
  all-subplots-with-topics endpoint (an N+1 fetch otherwise) — a genuinely
  separate feature, not implied by the rest of the request. Only the main
  Plot Viewer bar sits above the toggle now.
- **Excluded topics stay navigable in the carousel** (shown with the
  excluded icon) rather than being hidden, matching how `TopicCardGrid`
  already treated them (dashed/faded, not removed) — consistent with
  CLAUDE.md's framing of "excluded" as noise removed from *LLM* context,
  not from the author's own view.

Verified live against the real backend end-to-end, including the
highest-risk path: loaded a document, navigated Topic View and Theme View,
confirmed Save/Cancel still works, then asked the Sidekick in plain English
to exclude a specific topic by name — confirmed via a real LLM tool call
that it happened (`excluded: 1` in a fresh `/topics` fetch, matching the
exact topic ID the model reported), confirmed the UI's excluded icon
appeared without a page reload, then asked it to include the topic again
and confirmed that too (`excluded: 0`). No console errors at any point.
49 backend tests pass; frontend type-checks clean.

## Archived history (iterations 1-9, pre-refactor)

Kept for provenance. Describes UI surfaces that no longer exist as of
"Iteration 10" above (`Notecards.tsx`, `PlotViewer.tsx`, the old
per-section scoped `Sidekick`, the encoding-rule add/edit form, the
act-select dropdown). Do not use this section to understand current
behavior — see the Column layout / States / Gaps sections after it, which
were rewritten to describe the app as it exists now.

**Iteration 1** — done: CSS custom-property color palette (`--color-opening`/
`--color-conflict`/`--color-climax`/`--color-accent`); Hbar segments and
`TopicCardGrid` cards color-coded by act (left-border accent) instead of text
alone; every column wrapped in a bordered/padded `.panel`; native
`<details>/<summary>` accordion replacing the Documents Show/Hide button
(loading a document still auto-collapses it); document row hover highlight +
persistent highlight on the loaded row (Gap G2); `title` tooltips added to
every button across the app; Plot Viewer "← Clear selection" control (Gap
G3); Notecards empty-state message (Gap G9); global `box-sizing: border-box`
+ a `@media (max-width: 900px)` single-column collapse for narrow viewports
(Gap G11, partial — see note below). Not started, deliberately deferred (see
inline notes for why): the standard-file-dialog ingest flow, the Hbar → big
progress bar redesign, the click-nearest-topic carousel, and moving Sidekick
into the right column. Each is flagged below with what's blocking it.

**Iteration 2** — done: a shared `ToastContext` (`frontend/src/ToastContext.tsx`)
gives every mutation a consistent error banner instead of failing silently
(Gap G4 — fixed for every fetch in `App.tsx`, `Subplots.tsx`,
`EncodingRules.tsx`, and `Sidekick.tsx`); confirmation prompts added before
deleting an encoding rule or removing a topic from a subplot, matching
document delete (Gap G5 — fixed); a new "Remove from theme" action in
Notecards' theme detail, backed by a new `POST /topics/{id}/unassign-theme`
endpoint + `repository.unassign_topic_theme` (Gap G6 — fixed, with unit +
integration test coverage); an explicit "Subplots span all documents, not
just the loaded one" hint under the Subplots heading (Gap G1 — resolved by
making the scope explicit rather than filtering, to avoid hiding
intentionally cross-document subplots); a real loading state for the initial
page fetch (Gap G10 — fixed). Verified live: toast renders on a forced 500,
delete confirmations block on cancel, remove-from-theme updates the grid
immediately, all 32 backend tests pass. Not touched this pass: G7, G8, G12,
and the larger deferred items from iteration 1 (still open below).

**Iteration 3** — done: encoding rules can now be edited in place (Gap G7 —
fixed). `EncodingRules.tsx` reuses its existing add-rule form for both add
and edit (an Edit button per card populates the form and swaps "Add Rule"
for "Save Changes" + "Cancel"), backed by a new `PATCH /encoding-rules/{id}`
endpoint + `repository.update_encoding_rule`. Topics can now be manually
moved between acts (Gap G8 — fixed): every `TopicCardGrid` card can show a
small act `<select>` (color-matched to the palette), backed by a new
`POST /topics/{id}/set-act` endpoint + `repository.set_topic_act`; wired
into Plot Viewer and Notecards' theme detail (not Subplots — its structure
bar is chronological, not act-based, so reassigning act there would not
change what the user sees, and adding it would just be a second control
with no visible effect). Verified live: editing a rule's description
persists via the PATCH; reassigning a topic's act updates its card border
and the select's color immediately. All 35 backend tests pass; frontend
type-checks clean. Not touched this pass: G12, and the four larger
iteration-1 deferrals (still open below).

**Iteration 4** — done: the ingest flow now uses a real file dialog instead
of a typed folder path (Left Column TODO — fixed). `IngestForm.tsx` uses a
native `<input type="file" multiple>` (accepting .txt/.md/.docx/.pdf); the
Ingest button only renders once files are selected, exactly as asked. Files
upload one at a time to a new `POST /ingest/upload` endpoint
(multipart/form-data), backed by `service.upload_and_ingest`, which writes
into `draft_scripts/`/`story_notes/` (matching the selected role) and reuses
the existing single-file ingest pipeline — so it produces identical
documents/segments/styles to the folder-path route, just for a
browser-selected file instead of a server-side path. Filenames are
sanitized to their basename before being used as a path, since this
endpoint now takes untrusted client input. The old folder-path route
(`POST /ingest`) is untouched and still works for bulk/scripted ingestion;
only the UI's own form was replaced, per the TODO's wording ("replace the
text box... with a standard file dialog"). `python-multipart` added as a
backend dependency (required by FastAPI for form/file parsing) via
`uv add`. Verified live end-to-end: selected a real file via a synthetic
`DataTransfer`, confirmed the button only appears after selection, clicked
Ingest, confirmed the new document appears in the list and is queryable,
then cleaned up both the document and the file it wrote to disk. All 38
backend tests pass (3 new: upload creates a document, unsupported extension
is skipped, unknown role 400s — all against a monkeypatched `REPO_ROOT` so
tests never touch the real `draft_scripts/`/`story_notes/` folders).

**Iteration 5** — done: search/filter added where lists actually get long
(Gap G12 — partial, see below). `TopicCardGrid` now shows a search input
(filtering by title/summary, case-insensitive) whenever it has more than 6
topics — this one component is reused by Plot Viewer, Notecards' theme
detail, and Subplots' detail, so it covers every place a topic grid can
grow large in one change. Notecards' theme list gets the same treatment
above 6 themes. Both show a "No topics/themes match" message when the
filter has no results, and the threshold means small lists (which is most
of them, most of the time) show no extra UI at all — search only appears
when it would actually help, per the "without overwhelming" brief. Verified
live: loaded `document.docx`, opened its 22-topic theme, confirmed the
search box appears with the correct count, filtered "NTSB" down to the 2
matching topics, and confirmed the no-match state on a nonsense query — the
Sidekick below stayed scoped to all 22 topics throughout, since search is a
display filter only, not a context filter. Frontend-only change; all 38
backend tests still pass (untouched). G12 is not fully closed: no
pagination was added (lists still render in full, just filterable) and
Documents/Subplots/Encoding Rules lists have no search, since none of them
are anywhere near large enough yet to need it — revisit if that changes.

**Iteration 6** — done: two more Center Column TODOs, chosen because they
had concrete, checkable answers rather than open design questions.
"onMouseOver displays the page or chapter as a tooltip": `list_all_topics`
now resolves each topic's chapter (nearest preceding `Heading 1`-styled
segment in the same document) and PDF page number via two correlated
subqueries, exposed as `chapter_title`/`page_number` on `Topic`; the Hbar's
existing per-segment tooltip now appends "— Chapter Name" (or "— page N"
when there's no heading, i.e. PDF sources) after each topic title. Proven
correct with a unit test (heading segment → chapter_title, `page_number` on
the topic's segment → resolves both), but **not confirmed live**: no
document in the current dev database has both analyzed topics and
`Heading 1`-styled chapters at the same time (document.docx has topics but
no headings in its source file; manuscript.docx has headings from earlier
encoding-classifier work but was never analyzed into topics) — re-running
Reanalyze on manuscript.docx would prove it live but costs a real LLM call,
so this is flagged rather than forced. "Replace the Hbar with a larger
progress bar for the main plot" / "use smaller progress bars for
subplots": `ActHbar` takes a new `size` prop (`'large'` default, `'small'`
for Subplots' structure bar) — main Hbar is now 64px with a subtle shadow,
Subplots' is 28px with a smaller label. This is a deliberately conservative
reading of "larger progress bar": it makes the existing bar more visually
prominent and adds real size hierarchy between main-plot and subplot views,
without inventing a new bar-chart-style component the request did not
specify the shape of. Verified live: Plot Viewer's bar is visibly taller
with a shadow; a subplot's Structure bar is visibly thinner with smaller
text, right next to it in the same session for direct comparison. All 39
backend tests pass (1 new); frontend type-checks clean.

**Iteration 7** — done: Sidekick moved to the right column as a single
chat interface for everything (Center Column TODO — fixed). Resolved the
open design question — "what does 'everything' mean when nothing is
selected" — by reading the request literally: "for everything" means not
scoped to a narrow selection at all, not "whichever selection currently
wins." The three previous instances (Plot Viewer act, Notecards theme
detail, Subplot detail), each scoped to whatever was selected in that one
spot, are gone; there's now exactly one `<Sidekick>`, always visible at the
top of the right column above Encoding Rules, scoped to every active topic
in the loaded document regardless of what's selected anywhere else. This
is a real, deliberate narrowing of capability, not a pure win: you can no
longer ask a question scoped tightly to just one act or one theme the way
you could before — the tradeoff the request asked for. `Sidekick` gained an
empty state ("Load a document...") for when nothing is loaded, since it's
now always rendered instead of conditionally appearing only when something
was selected. Verified live end-to-end against the real backend: loaded
document.docx, confirmed exactly one `.sidekick-input` exists on the page
(before and after selecting a Plot Viewer act, proving the old per-section
instances are gone, not just hidden), asked "Who is the protagonist?" and
got a real LLM answer back citing Felicia Martin. Frontend-only change;
all 39 backend tests pass untouched.

Right Column TODOs remain blocked: "encoding rules display-only" and "AI
sidekick manages it" both depend on giving the sidekick's LLM call
tool-use/write access to the encoding-rules endpoints — today
`sidekick.llm.answer_question` only ever reads topics context and returns
prose, it has no function-calling loop. That is a backend AI-capability
build (tool definitions, multi-turn tool-call handling, execution), not a
UI change, and deserves its own iteration rather than a rushed bolt-on.
Making encoding rules read-only *now*, before that exists, would strand
the user with no way to manage rules at all — a real regression — so it
was deliberately left alone.

The one item left unstarted from the original TODOs is the
click-nearest-topic carousel (centered topic + prev/next neighbors, a
vertical position marker on the Hbar, theme-linked visual grouping, topics
nested under their theme). It remains a genuinely new interaction pattern
with seven distinct sub-behaviors specified — the kind of thing that needs
a mockup or a real back-and-forth to get right, not a best-guess
implementation that risks shipping something confusing under the banner of
"improving" it.

**Iteration 8** — two things, deliberately chosen because the two
remaining large TODOs (the carousel, and AI-managed encoding rules) both
carry real risk if guessed wrong rather than just being time-consuming:

1. A full regression pass across everything built in iterations 1-7 (never
   done end-to-end in one sitting before). Console clean on load; loaded
   document.docx and walked Plot Viewer act select/clear, Notecards
   search + theme detail + back, Encoding Rules, and Sidekick with no
   errors. Caught and fixed one real problem along the way — but it was in
   my *test script*, not the app: an early ad-hoc regression check used
   `document.querySelector('.act-select')` positionally instead of by
   topic id, and when reassigning a topic's act moved it out of the
   filtered view being tested, the "revert" step grabbed a *different*
   topic's dropdown and silently left the real one changed. Found it by
   noticing the Conflict-bucket count had shifted by exactly one (67 to
   66) between checks, traced it to topic id 13 ("Meeting Erin
   Michelson"), and reset it via the set-act endpoint directly. Data is
   back to its original state (6/67/3 across Opening/Conflict/Climax),
   confirmed by a fresh fetch. Noted here because the actual application
   code was never at fault, but the incident is worth recording — direct
   DOM manipulation for regression testing needs to track entities by id,
   not by re-querying a selector after a mutation may have changed what
   that selector matches.
2. Pulled one genuinely safe, additive piece out of the carousel spec
   without touching the rest of it: "the Hbar shows a vertical line where
   the active topic lives in the story." Hovering any topic card now
   draws a thin vertical marker on its Hbar at that topic's proportional
   position among every topic in that bar's own scope (the whole document
   for Plot Viewer, the subplot's own topics for Subplots' structure
   bar), and the marker disappears on mouse-leave. No existing behavior
   changed — click-to-select, the tooltip, search, and act reassignment
   all work exactly as before; this is a pure hover-only addition.
   Deliberately *not* attempted: the centered/prev/next carousel replacing
   the current click-a-segment-see-a-grid interaction, and the
   theme-linked visual grouping — both are still the multi-part
   redesign flagged in iteration 7, unstarted for the same reason.

Verified live: marker appears on hover (confirmed via `mouseover`/
`mouseout` dispatch and a zoomed screenshot showing it at the
Opening/Conflict boundary, matching the hovered topic's real sequence
position), disappears on `mouseout`. All 39 backend tests pass
(untouched — frontend-only change); frontend type-checks clean.

**Iteration 9** — surveyed `UI.md` for every remaining unchecked item
before touching anything: only three are left ("bootstrap layout" —
deliberately declined with a documented reason; the two AI-manages-
encoding-rules items — genuinely blocked on the same LLM tool-calling
build) plus the partial carousel. Rather than force one of the two
already-declined large items a third time, found and fixed a real,
previously unflagged gap instead: **no clickable card, tag, or Hbar
segment in the whole app was keyboard-accessible.** Six places
(`ActHbar`'s act segments and unassigned segment, Notecards' theme cards
and Unassigned Topics card, Subplots' subplot cards, `TopicCardGrid`'s
theme tag-link) were `<div>`/`<span>` elements with only an `onClick` —
no `tabIndex`, no `role`, no keyboard handler, meaning a keyboard-only or
screen-reader user could not open a theme, a subplot, an act, or follow a
theme link anywhere in the app. Added a small shared helper
(`keyboardActivate.ts`) and wired `role="button"`, `tabIndex={0}`, an
`aria-label`, and an Enter/Space handler into all six, plus a
`:focus-visible` outline in the app's accent color so keyboard focus is
actually visible. Known imperfection, noted rather than hidden: the theme
and subplot cards still nest their own Edit/Exclude/Promote buttons
inside an outer `role="button"` element, which strict ARIA authoring
practice discourages (a button containing other interactive elements) —
fixing that properly means restructuring those cards (e.g. splitting the
"open" affordance from the action buttons), which is a real layout change
this iteration didn't attempt. Verified live: focused an Hbar segment and
a theme card via `.focus()`, confirmed `document.activeElement` matched,
dispatched a real `Enter` `keydown`, and confirmed both actually
activated (the Hbar selection changed; the theme detail view opened) —
not just that a handler existed. Frontend-only change; all 39 backend
tests pass untouched; frontend type-checks clean.

---

## Layout overview (current)

- Single page, no routing. One `<h1>` above a three-column CSS grid.
- Grid: Documents (15%) | Center (70%, content capped to 700px and centered
  inside that column) | Encoding Rules + Sidekick (15%). Column gap scales
  with viewport (`clamp(1rem, 4vw, 4rem)`); collapses to one column under
  900px.
- `<h1>` reads "Genre Writer" until a document is loaded, then becomes the
  loaded document's filename.
- Every column/section is wrapped in a `.panel` (bordered, padded) for
  visual separation; every actionable element has a `title` tooltip and is
  keyboard-reachable (`role="button"` + `tabIndex` + Enter/Space where it
  isn't already a native button).

---

## Column layout (top to bottom)

### Left column — Documents
Unchanged from the archived history: native multi-file picker (Ingest
button only appears once files are chosen), a `<details>` accordion
document list (auto-collapses on Load), four icon buttons per document
(Load, Reanalyze, Classify Encoding, Delete), the loaded row highlighted.

### Center column — Plot Viewer, then the Topic/Theme carousel, then Subplots
1. **"Plot Viewer" heading** + the main Hbar (`HbarVisual`, `size="large"`):
   Opening/Conflict/Climax segments sized proportionally to active topic
   count (+ an "Unassigned" segment if any topics have no act), a tooltip
   listing that segment's topics on hover, and a vertical position marker
   showing where the carousel's current topic sits. Clicking a segment
   jumps the shared current-topic pointer to that act's first topic — it
   no longer opens a grid underneath itself; the carousel below is what
   displays topics now.
2. **`PlotCarousel`** (no heading of its own — the Topic View / Theme View
   toggle is the header): see States S1-S4 below for the two modes.
3. **"Subplots" heading** — completely unchanged from the archived
   history: global (all documents) hint, "+ New Subplot", subplot card
   grid, and a detail view with its own small `ActHbar` (`size="small"`),
   add-topic control, and `TopicCardGrid` (Exclude/Remove buttons still
   present here — Subplots was explicitly out of scope for the
   Sidekick-drives-everything change; see "Iteration 10" above).

### Right column — Encoding Rules, then Sidekick
1. **"Encoding Rules" heading** + a plain list of rule pills (label or
   description text in a rounded pill). No buttons, no form — display
   only.
2. **"Sidekick" heading** + `Sidekick`: an answer area (shows the most
   recent answer, or a hint about what it can do) and a question input +
   Ask button, always visible regardless of what's loaded.

---

## States

### S0 — Backend unreachable (error)
Unchanged: the whole layout is replaced by one line of red text.

### S1 — No document loaded
- **Center:** main Hbar shows three empty buckets; `PlotCarousel` shows
  "Load a document and analyze it to browse its topics and themes here."
  (with the Topic/Theme toggle still visible, non-functional); Subplots is
  fully functional (global scope, unaffected by document state).
- **Right:** Encoding Rules always shows all rules; Sidekick shows "Load a
  document, then ask the sidekick to look up, change, or organize anything
  in it."

### S2 — Document loaded
- **Trigger:** Load icon on a document row.
- **Effect:** title becomes the filename; Documents list auto-collapses;
  the carousel's current-topic pointer resets to the new document's first
  topic (by `sequence_index`).
- Main Hbar and `PlotCarousel` now show this document's topics/themes.
  Subplots stays global/unaffected (unchanged from before).

### S3 — Carousel: Topic View (default)
- **Displayed:** Previous / Current / Next tiles (real topic titles, act
  color, theme/excluded `StatusIcon`s) with the current tile visually
  emphasized; below, an Editor box showing the current topic's title,
  summary, and status icons, plus a single **Edit** button.
- **Functionality:** click a Previous/Next tile (or use the main Hbar) to
  move the current-topic pointer; click Edit to enter S5. Nothing else —
  excluding, promoting, unassigning from a theme, and reassigning act all
  moved to the Sidekick (see S6).

### S4 — Carousel: Theme View
- **Trigger:** the "Theme View" toggle button.
- **Displayed:** Previous / Current / Next theme tiles; below, a
  two-column row — the Current Theme Editor (title, summary, Edit button)
  on the left, a grid of that theme's topics-as-icons on the right (each a
  small tile with the excluded icon if applicable and a truncated title).
- **Functionality:** navigate themes; click Edit to enter S5 (theme
  variant); click any topic icon to jump straight to it in Topic View
  (S3), switching the toggle automatically.

### S5 — Carousel: editing (topic or theme)
- **Trigger:** the Edit button in either view's Editor box.
- **Displayed:** the Editor box's content is replaced by `CardEditForm` —
  title input, summary textarea, **Save** and **Cancel** buttons. Kept
  exactly as before per explicit instruction; this is the only mutation
  still reachable through a direct UI control rather than the Sidekick.
- **Functionality:** Save (PATCH) or Cancel, returning to S3/S4.

### S6 — Sidekick drives everything else
- **Trigger:** typing a request and clicking Ask (or Enter).
- **Request scope:** every active (non-excluded) topic in the loaded
  document is sent as context, plus every encoding rule (rules are
  global, not document-scoped). The model can still act on an excluded
  topic if the user names its ID directly, since excluded topics are
  filtered out of context but tool execution doesn't re-check membership.
- **What it can do:** answer questions about the given topics/themes/
  rules in prose, or call one of 8 tools — exclude/include a topic or
  theme, remove a topic from its theme, promote a theme to a subplot,
  reassign a topic's act, add/edit/delete an encoding rule. Each tool maps
  directly to an existing, already-tested repository function.
- **Effect on the rest of the UI:** the response includes `actions: string[]`
  (which tools ran, if any); the frontend refetches topics, themes,
  subplots, and encoding rules whenever `actions.length > 0`, so the
  carousel/Hbar/Encoding Rules panel reflect the change without a reload.
- **Functionality it deliberately does not have:** editing a title/summary
  (that stays a direct UI action, S5) or anything touching Subplots or
  document ingest/analysis (out of scope, see "Iteration 10" above).

### S7 — Document row async status (transient, per document)
Unchanged: Reanalyze/Classify Encoding show an inline "…ing" then result
tag; Delete is confirmed; Load is instant.

---

## Gaps / implied missing functionality (current)

Most gaps from the archived history were about UI surfaces (Notecards,
per-section Sidekick, the encoding-rule form) that no longer exist, so
they're not restated here. What's still true or newly true:

- [ ] **The stacked/nested mini-bars from the mockup aren't rendered as an
  always-visible summary of every subplot.** Only Subplots' own detail
  view shows its small bar (unchanged from before). Building an
  always-visible row of per-subplot bars needs a new bulk endpoint
  (today, a subplot's topics are only fetched on demand when you open its
  detail) — see "Iteration 10" above for the full reasoning.
- [ ] **No conversation history in Sidekick.** Each ask is a fresh
  request; there's no follow-up context from a previous question in the
  same session, so "and also exclude the next one" wouldn't know what
  "the next one" refers to without repeating it.
- [ ] **No confirmation before a Sidekick tool call executes.** Direct UI
  actions like document delete or encoding-rule delete (when that existed)
  asked first; a Sidekick-driven exclude/promote/delete-rule happens
  immediately based on the model's own judgment of what was asked. Given
  every tool maps to a reversible-ish action (nothing hard-deletes data
  except `delete_encoding_rule`, which only removes a rule definition, not
  any classified content), this was accepted as a reasonable tradeoff for
  a natural-language interface, not an oversight — but worth revisiting if
  it causes real friction.
- [ ] **Subplots' own topic grid still has Exclude/Remove buttons and no
  Sidekick integration**, since it was explicitly out of scope for this
  refactor. Whether that's a permanent split or should eventually match
  the rest of the app is an open product question, not a bug.
- [ ] **G12 (old) — search/pagination** — unchanged from before: search
  exists on `TopicCardGrid` (used by Subplots) above 6 items; the new
  carousel doesn't need it (it shows one topic/theme at a time by design).
