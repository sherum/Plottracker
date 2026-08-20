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
1. "Documents" heading + Show/Hide toggle button (controls the list below only)
2. Ingest form: folder path input, role select (`draft_script`/`story_note`), Ingest button
3. Document list (hidden when toggled off): per document —
   filename, role tag, then four icon buttons (Load, Reanalyze, Classify
   Encoding, Delete), then a transient status tag if Reanalyze or Classify
   Encoding is in flight/just finished
### Left Column TODOs
- [x] Use an accordion component, remove the hide/show — replaced the button + `documentsCollapsed` toggle with native `<details>/<summary>`. `documentsCollapsed` state kept (renamed use) only so loading a document can still auto-collapse the list; the manual button is gone.
- [x] onHover on a button shows tool tip with its name — done app-wide, not just this column.
- [x] onMouseOver changes the document title css to give a visual clue that it has the mouse focus — filename underlines and recolors on row hover.
- [ ] replace the text box, selector and ingest with a standard file dialog — **not started.** This is a full-stack change, not a UI swap: the backend's `/ingest` only accepts a server-side folder path (`ingest_folder`); a real file-picker needs a new multipart upload endpoint that writes the uploaded bytes into `draft_scripts/`/`story_notes/` before running the existing extractor. Needs its own iteration with backend + frontend + tests, not a rushed partial version.
- [ ] The ingest button appears after a file is selected — blocked on the above; same iteration.
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
- **Functionality:** each topic card is independently editable/excludable in place (`TopicCardGrid`'s own edit state); no "remove from theme" action exists here (Gap G6). Back returns to S4.

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
- **Functionality:** add a rule (style_kind, block_length, position, label, description), delete a rule. No edit-in-place (Gap G7). Not scoped to any document — rules are global and only take effect when a document's Classify Encoding is run.

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

- [ ] **G1 — Subplots isn't scoped to the loaded document.** Plot Viewer and Notecards filter to the loaded document's topics/themes; Subplots always shows every subplot from every document. Either scope it the same way, or make the global scope explicit in the UI (e.g., a note or its own "all documents" label).
- [x] **G2 — No visual indicator of which document is loaded, inside the Documents list itself.** Fixed: the loaded row now gets an accent border + tinted background (`.documents-list li.loaded`).
- [x] **G3 — Plot Viewer has no back/deselect control.** Fixed: added a "← Clear selection" button in `ActHbar`, shown whenever a segment is selected.
- [ ] **G4 — No error handling on any mutation.** Ingest, reanalyze, classify, delete, promote, add/remove topic, add/delete encoding rule, Sidekick ask — all `fetch` calls assume success. A failed request fails silently (no toast, no inline error).
- [ ] **G5 — Delete is the only destructive action with a confirmation.** Deleting an encoding rule and removing a topic from a subplot both fire immediately with no confirmation, inconsistent with document delete's `window.confirm`.
- [ ] **G6 — No "remove topic from theme" action.** `TopicCardGrid` supports `onRemoveTopic` (used in Subplots' detail view) but Notecards never passes it, so a topic can only be excluded, never unlinked from its theme, via the UI.
- [ ] **G7 — Encoding rules can't be edited**, only added or deleted; fixing a typo in a label means delete-and-recreate.
- [ ] **G8 — No manual act reassignment.** Plot Viewer's Opening/Conflict/Climax buckets are entirely LLM-assigned (`topic.act`); there's no UI to move a topic between acts or into/out of "Unassigned".
- [x] **G9 — Inconsistent empty-state messaging.** Fixed: Notecards now shows a hint matching Plot Viewer/Subplots when there's nothing to display.
- [ ] **G10 — No loading state for the initial page fetch.** Between mount and the `Promise.all` resolving, the page renders a fully empty shell with no spinner or skeleton.
- [~] **G11 — No responsive/narrow-viewport layout.** Partially fixed: `.layout` now collapses to one column under 900px viewport width. Not yet verified in an actual narrow browser window — the change is syntactically standard CSS but should get a manual resize check.
- [ ] **G12 — No search or pagination** anywhere (documents, topics, themes, subplots, encoding rules) — every list renders in full.
