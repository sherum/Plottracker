# UI.md

Purpose: describe the Genre Writer frontend as it actually behaves today — its
states, what functionality is reachable from each, and what each column shows
top to bottom. This file is meant to be edited (annotate, correct, add `FIX:`
notes under any state or gap) and then handed to an MCP-driven UI agent as the
spec for what to change. Keep the structure intact (state template, column
template, checklist gaps) so an agent can diff future UI behavior against it.

Source of truth: `frontend/src/App.tsx` and the components it renders
(`IngestForm`, `Notecards`, `PlotViewer`/`ActHbar`, `Subplots`, `EncodingRules`,
`TopicCardGrid`, `CardEditForm`, `Sidekick`, `IconButton`).

## Progress log

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

---

## Layout overview

- Single page, no routing. One `<h1>` above a three-column CSS grid.
- Grid: Documents (15%) | Center (70%, content capped to 700px and centered
  inside that column) | Encoding Rules (15%). Column gap scales with viewport
  (`clamp(1rem, 4vw, 4rem)`).
- `<h1>` reads "Genre Writer" until a document is loaded, then becomes the
  loaded document's filename. This is the only global state indicator.
### Layout TODOs
- [ ] Change to bootstrap layout — **not done.** Implemented the same effect (fluid scaling + narrow-viewport collapse) with native CSS Grid + a `@media (max-width: 900px)` breakpoint instead of pulling in the Bootstrap framework — adding a whole CSS framework as a dependency for one page contradicts this codebase's existing hand-rolled CSS and the project's "don't over-engineer" convention. Revisit only if a real reason for the framework itself (not just its grid) shows up.
- [x] The app always scales to the screen to retain outside margins or collapses when reduced to smaller formats — fluid `clamp()` gap + percentage columns already scaled; added the `@media (max-width: 900px)` single-column collapse. Not yet verified at an actual narrow browser window (the automation's resize tool wasn't cooperating) — worth a manual check.
- [x] All buttons are tool tip enabled — `title` attributes added to every button in every component.
- [~] Component never dangle outside of their parent container's border — added global `box-sizing: border-box` and panel padding; not exhaustively audited. Known remaining risk: `.hbar-tooltip` is centered on its segment and can overflow the panel/viewport near the left/right edges.
- [x] Containers are padded top and bottom, left and right to make each one distinct — `.panel` class applied to all three columns and each center-column section.
- [x] Containers can use tool tips — panels don't have their own tooltip, but every actionable element inside them does.
- [x] The full color pallet will be used to visually link related elements at a glance — `--color-opening/conflict/climax` tie Hbar segments to `TopicCardGrid` card borders by act. Themes/subplots don't have their own color coding yet (would need a deterministic hash-to-color scheme — noted as a possible follow-up, not started).

---

## Column layout (top to bottom)

### Left column — Documents
1. "Documents" heading
2. Ingest form: native file picker (multi-select, .txt/.md/.docx/.pdf), role
   select (`draft_script`/`story_note`), Ingest button (only rendered once
   files are selected)
3. Document list, inside a native `<details>` accordion (open by default;
   loading a document auto-collapses it): per document —
   filename, role tag, then four icon buttons (Load, Reanalyze, Classify
   Encoding, Delete), then a transient status tag if Reanalyze or Classify
   Encoding is in flight/just finished
### Left Column TODOs
- [x] Use an accordion component, remove the hide/show — replaced the button + `documentsCollapsed` toggle with native `<details>/<summary>`. `documentsCollapsed` state kept (renamed use) only so loading a document can still auto-collapse the list; the manual button is gone.
- [x] onHover on a button shows tool tip with its name — done app-wide, not just this column.
- [x] onMouseOver changes the document title css to give a visual clue that it has the mouse focus — filename underlines and recolors on row hover.
- [x] replace the text box, selector and ingest with a standard file dialog — fixed in iteration 4: `IngestForm.tsx` now uses `<input type="file" multiple>`, uploading to a new `POST /ingest/upload` endpoint that reuses the existing single-file ingest pipeline.
- [x] The ingest button appears after a file is selected — fixed alongside the above; the button is conditionally rendered, not just disabled.
- [x] center and justify all elements in the left column — `.col-documents` is centered; ingest inputs/selects/buttons stretch full width; doc-action icons are centered per row.

### Center column — Plot Viewer, Notecards, Subplots (in that order)
1. "Plot Viewer" heading, then the Hbar (Opening/Conflict/Climax segments
   sized proportionally to active topic count, plus an "Unassigned" segment
   if any topics have no act), then either a hint line or the selected
   segment's topic card grid + Sidekick
2. "Notecards" heading, then either the theme card grid (+ "Unassigned
   Topics" card) or a selected theme's back button + summary + topic card
   grid + Sidekick
3. "Subplots" heading, then either the subplot card grid (+ "New Subplot")
   or a selected subplot's back button + summary + its own recursive
   three-act Hbar + add-topic control + topic card grid + Sidekick
### Center Column TODOs
- [ ] replace the Hbar with a larger progress bar for the main plot — **not started.** This is a visual redesign of the core navigation widget with real interaction-design decisions to make (what does "larger" mean for a proportionally-segmented bar? does click-to-select still work the same way?) — deserves its own focused iteration rather than a rushed reshape.
- [ ] use smaller progress bars for subplots — blocked on the above (Subplots reuses the same `ActHbar` component; redesigning one redesigns both).
- [x] Use colors to separate the three act structure, not text i.e "Conflict" — done (see Layout TODOs); applies to both the main Plot Viewer and each Subplot's own structure bar since they share `ActHbar`.
- [ ] onMouseOver displays the page or chapter as a tooltip — **not started.** `Topic` doesn't currently carry a page/chapter number to the frontend (segments have `page_number`/`paragraph_index` server-side, but topics aren't joined to that today) — needs a data-model check before it's a UI change.
- [ ] clicking the Hbar will select the nearest topic (carousel: centered topic + prev/next neighbors, vertical position marker, theme-linked visual grouping, topics nested under their theme the way they nest under the Hbar) — **not started.** This is a large new interaction pattern, not a tweak; needs its own design pass.
- [ ] Move the AI sidekick to the right column as a single chat interface for everything — **not started.** Today `Sidekick` is instantiated three separate times (Plot Viewer act, Notecards theme, Subplot detail), each scoped to whatever topics are currently selected. Moving to one global instance means deciding what "everything" means when nothing is selected, and threading the currently-selected topics up to wherever it lives. Worth doing deliberately, not as a drive-by move.

### Right Column TODOs
- [ ] Refactor the encoding rule to be a display only — **not started.**
- [ ] The AI sidekick will manage it — **not started**, blocked on the Sidekick relocation above, and on giving the sidekick's LLM call tool-use access to the encoding-rules endpoints (currently `Sidekick`/`sidekick.llm.answer_question` only ever reads topics, it has no write path).

---

## States

Each state below follows the same template: what triggers it, what each
column shows, and what the user can actually do.

### S0 — Backend unreachable (error)
- **Trigger:** the initial `Promise.all` fetch of documents/themes/topics/subplots/encoding-rules fails.
- **Displayed:** the entire three-column layout is replaced by one line of red text. No columns, no title.
- **Functionality:** none. No retry button; only a page refresh recovers.

### S1 — No document loaded (initial state)
- **Trigger:** app just loaded, or the loaded document was just deleted.
- **Title:** "Genre Writer".
- **Left:** ingest form + full document list, functional.
- **Center:** Plot Viewer shows three empty act buckets (no topics, hint text only); Notecards shows an empty-state message (Gap G9 — fixed); Subplots shows **all** subplots across all documents (not scoped to "no document loaded" — see Gap G1).
- **Right:** unaffected by document state; always shows all encoding rules.
- **Functionality:** ingest, load/reanalyze/classify/delete any document, manage encoding rules, browse/create subplots. Plot Viewer and Notecards have nothing to show yet.

### S1 TODOs
- 

### S2 — Document loaded
- **Trigger:** user clicks the Load icon on a document row.
- **Effect:** title becomes the filename; Documents list auto-collapses (`documentsCollapsed = true`).
- **Center:** Plot Viewer and Notecards now filter to topics/themes whose `document_filename` matches the loaded document.
- **Right / Subplots:** unchanged — still global, not filtered to the loaded document (Gap G1).
- **Functionality:** same as S1 plus the center column now has real content to browse.
### S2 - TODOs
- [x] Tool Tips — done app-wide, see Layout TODOs.

### S2a — Documents list shown/hidden
- **Trigger:** the Show/Hide button next to "Documents".
- Independent of S1/S2 — toggling does not affect `loadedDocument`. Hidden state keeps the ingest form visible, hides only the `<ul>`.

### S3 — Plot Viewer: act selected
- **Trigger:** click an Hbar segment (Opening/Conflict/Climax/Unassigned).
- **Displayed:** that act's topic card grid + a Sidekick chat scoped to its active topics; a "← Clear selection" button above the grid.
- **Functionality:** edit/exclude any topic card in place; ask Sidekick questions about this act only; clear the selection to return to the hint state (Gap G3 — fixed).

### S3 - TODOs

### S4 — Notecards: theme list (default)
- **Trigger:** default view, or navigating back from a theme/unassigned detail.
- **Displayed:** grid of theme cards (title, summary, active topic count, Edit/Exclude/Promote), plus an "Unassigned Topics" card if any topic has no theme.
- **Functionality:** edit a theme inline (→ S5), exclude/include a theme, promote a theme to a subplot, click a card to open its detail (→ S6).

### S4 - TODOs

### S5 — Notecards: theme editing
- **Trigger:** Edit button on a theme card.
- **Displayed:** that card is replaced in place by `CardEditForm` (title input, summary textarea, Save/Cancel).
- **Functionality:** save (PATCH the theme) or cancel back to S4.

### S5 - TODOs

### S6 — Notecards: theme/unassigned detail
- **Trigger:** clicking a theme card body, or the "Unassigned Topics" card.
- **Displayed:** "← Themes" back button, theme title (+ summary, unless unassigned), topic card grid, Sidekick scoped to these topics.
- **Functionality:** each topic card is independently editable/excludable in place (`TopicCardGrid`'s own edit state); a topic card also shows "Remove from theme" (not shown for Unassigned, since there's nothing to remove it from) — Gap G6, fixed. Back returns to S4.

### S6 - TODOs

### S7 — Subplots: list (default)
- **Trigger:** default view, or navigating back from a subplot detail.
- **Displayed:** "+ New Subplot" control, grid of subplot cards (title, summary, topic count, source theme tag if promoted).
- **Functionality:** start creating a subplot (→ S8), click a card to open its detail (→ S9).

### S7 - TODOs

### S8 — Subplots: creating
- **Trigger:** "+ New Subplot".
- **Displayed:** `CardEditForm` in place of the "+ New Subplot" button.
- **Functionality:** save (POST a new subplot, returns to S7) or cancel.

### S8 - TODOs

### S9 — Subplots: detail
- **Trigger:** clicking a subplot card.
- **Displayed:** "← Subplots" back button, title, summary, "Structure" heading with its own recursive three-act Hbar (topics split evenly by chronological order, not LLM-assigned act), "All Topics" heading with an add-topic dropdown (any topic app-wide not already a member) + Add button, then the full topic card grid (with Remove, unlike S6) and a Sidekick scoped to this subplot.
- **Functionality:** add any topic from any document to this subplot, remove a topic, edit/exclude topics in place, ask Sidekick about this subplot only.

### S9 - TODOs

### S10 — Encoding Rules (single state, no navigation)
- **Displayed:** rule card grid + always-visible add-rule form.
- **Functionality:** add a rule (style_kind, block_length, position, label, description), edit a rule in place via the same form (Gap G7, fixed), delete a rule. Not scoped to any document — rules are global and only take effect when a document's Classify Encoding is run.

### S10 - TODOs

### S11 — Document row async status (transient, per document)
- **Reanalyze:** button click → "Analyzing…" tag → "Done: X topics, Y themes created".
- **Classify Encoding:** button click → "Classifying…" tag → "Tagged N segments".
- **Delete:** blocked behind a native `window.confirm`; no status tag, no undo.
- **Load:** instant, no status tag.
- These statuses persist in component state until the next reanalyze/classify of the same document; they are not cleared by navigating away or loading a different document.

---

## Gaps / implied missing functionality

Not yet built, but implied by the states above. Each is independent — pick
any subset to hand to the MCP agent.

- [x] **G1 — Subplots isn't scoped to the loaded document.** Resolved by making the scope explicit: a "Subplots span all documents, not just the loaded one" hint now sits under the heading. Deliberately not filtered — subplots can legitimately mix topics from multiple documents (the add-topic dropdown in subplot detail already draws from every document), so hiding subplots that reference other documents would hide real membership, not noise.
- [x] **G2 — No visual indicator of which document is loaded, inside the Documents list itself.** Fixed: the loaded row now gets an accent border + tinted background (`.documents-list li.loaded`).
- [x] **G3 — Plot Viewer has no back/deselect control.** Fixed: added a "← Clear selection" button in `ActHbar`, shown whenever a segment is selected.
- [x] **G4 — No error handling on any mutation.** Fixed: a shared `ToastContext` shows a dismissible error banner on any failed fetch, wired into every mutation in `App.tsx`, `Subplots.tsx`, `EncodingRules.tsx`, and `Sidekick.tsx`. Verified by forcing a 500 response and confirming the toast renders.
- [x] **G5 — Delete is the only destructive action with a confirmation.** Fixed: deleting an encoding rule and removing a topic from a subplot now confirm first, same pattern as document delete. Verified the confirm fires with the correct label and a cancel leaves the rule in place.
- [x] **G6 — No "remove topic from theme" action.** Fixed: a "Remove from theme" button now appears on topic cards inside Notecards' theme detail view (not shown for "Unassigned Topics", since there's no theme to remove from), calling a new `POST /topics/{id}/unassign-theme` endpoint. Verified the topic disappears from the theme's grid immediately.
- [x] **G7 — Encoding rules can't be edited.** Fixed: an Edit button per rule card opens the same form used to add one, PATCHing instead of POSTing.
- [x] **G8 — No manual act reassignment.** Fixed: topic cards in Plot Viewer and Notecards now have an act `<select>` (Opening/Conflict/Climax/Unassigned) that calls the new set-act endpoint. Not wired into Subplots' topic grid — its structure bar buckets by chronological order, not `topic.act`, so the control would have no visible effect there.
- [x] **G9 — Inconsistent empty-state messaging.** Fixed: Notecards now shows a hint matching Plot Viewer/Subplots when there's nothing to display.
- [x] **G10 — No loading state for the initial page fetch.** Fixed: a `loading` state renders "Loading Genre Writer…" until the initial `Promise.all` settles (success or failure), instead of an empty shell.
- [x] **G11 — No responsive/narrow-viewport layout.** Fixed and verified: `.layout` collapses to one column under 900px; confirmed live at a 700px viewport — Documents, Plot Viewer, Notecards, and Subplots stack cleanly with no overflow.
- [~] **G12 — No search or pagination.** Partially fixed: `TopicCardGrid` and Notecards' theme list now show a search filter once they pass 6 items (covers Plot Viewer, Notecards, and Subplots' topic grids in one change, since they share `TopicCardGrid`). Documents, Subplots, and Encoding Rules still have no search and nothing has pagination — none of those lists are large enough yet to need it.
