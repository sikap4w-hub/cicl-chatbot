# Paper Review — Analysis Only (No Rewriting Yet)

Manuscript reviewed: *Integration of Taglish Speech-to-Text and an Applied Legal Consequence Game to an NLP-Based Chatbot Support System for Children in Conflict with the Law* (uploaded version, defense date now September 16, 2026).

This is Stage 1 only, per your instruction: assessment, change matrix, and consistency check. Nothing has been rewritten. Where I reference "the actual system," I am cross-checking against the real codebase (`gemini_engine.py`, `intent_engine.py`, `law_retrieval.py`, `main.py`, `game_data/*.json`, `static/script.js`) that this same project has been building this session, not assumptions.

---

## A. CURRENT PAPER ASSESSMENT

### Strong sections (leave alone)
- **Chapter 1 (Introduction)**: background, statement of the problem, research questions, general/specific objectives, significance, and definition of terms are well-written, internally consistent with each other, and properly cited. This is publication-quality academic prose already — do not rewrite it.
- **Chapter 2 (RRL)**: five thematic sub-sections mapped 1:1 to the five SOPs, each anchored on exactly five studies from the last five years, closing with a synthesis paragraph that ties back to the research gap. This structure is a genuine strength and should be preserved as the template for any future RRL expansion.
- **Reference list**: 26 entries, APA 7 formatted, DOIs present on nearly every entry, all within the five-year window except the two laws (correctly exempted per your own convention). This is in noticeably better shape than my last read of this project's notes suggested ("three references with incomplete details") — that issue appears already resolved. I did not find a citation in-text that is missing from the list, or vice versa, in the sections I checked.
- **Chapter 3 methodology (3.2 onward)**: the per-SOP "Process / Tools / System Models" structure is thorough, the figure/DFD numbering is internally consistent, and the two `[INFORMATION NEEDED]` markers (ASR model variant, intent library, corpus specifics) and the stale "2 of 20 cases ready" line were already corrected in a prior pass this session to reflect the real state of the build (Whisper-small + Hugging Face pipeline named, scikit-learn intent classifier named, all 20 cases now ready).

### Weak / outdated / unfinished sections
- **Abstract**: still literal template placeholder text ("The maximum length of the abstract is one to two pages... Use 12-point Times New Roman...") — not written at all.
- **Acknowledgements**: same problem — only the generic CISTM thank-you to the formatting assistant is there; no actual acknowledgements from you or Jamie.
- **Table of Contents**: has not been rebuilt since the CISTM template was filled in. It still shows placeholder headings from the template itself — "1.2 Fonts," "1.3 Paragraphs and Line Spacing," "1.3.1 Section numbering," "1.3.2 Lists," "2.1 Referencing within the Text," "3.1 Equations," "4.1 SI Units," "4.2 Figures," "5.1 Tables" — none of which exist anywhere in your actual Chapter 1–4 body text. A panel member opening the ToC will not find a single real heading in it.
- **Appendices**: the appendix list at the end of the document is also unedited template content and does not describe your actual appendices. It literally reads "APPENDIX B: simulation... APPENDIX c: ICP -- OES AND AAS ANALYSIS / source code... APPENDIX D: JOURNAL paper." "ICP-OES and AAS analysis" is chemistry/materials-science lab terminology — it has nothing to do with a software capstone and was clearly never replaced. It also contradicts the front-matter Table of Contents, which lists only "APPENDIX A: GANTT CHART" and "APPENDIX B: MATERIAL SAFETY DATA SHEETS (MSDS)" — again chemistry-lab template language, not appendices a software project would have.
- **Table 3.1 (Sprint Schedule)**: Sprint 9 (Aug 31–Sep 4, 2026) is still labeled "In Progress (current sprint)," but today's date has already passed September 4. There is also now an unaccounted gap between Sept 4 (end of Sprint 9) and Sept 16 (the newly moved defense date) with no sprint covering it.
- **Chapter 4**: every results table is `[RESULTS PENDING]` by design, because the STT and NLP-retraining modules genuinely are not built yet. This is honest and appropriate for a Title/Proposal defense — flagged here only so it's not mistaken for an oversight.

### Missing information
- ASR model version pins, intent-classifier library version pins (flagged in-text already as needing a `pip freeze` once the environment is finalized).
- Real WER / intent-accuracy / SUS figures (post-defense work, cannot be filled now).
- Actual abstract and acknowledgements content.

### Contradictions found (see Consistency Check table for the full list)
1. **Game scope, Chapter 1/2 vs. Chapter 3.** Chapter 1's Scope and Chapter 2's Conceptual Framework both describe the game as "at least ten storyboard-based case-review scenarios, each depicting an offense." Chapter 3 (SOP 3) describes 20 total cases — 10 depicting offenses and 10 depicting positive conduct — and frames the inclusion of the positive-conduct half as a deliberate, load-bearing design decision (it is what prevents the game from depicting CICL characters solely as offenders, which is directly relevant to Rule 5 of your own review instructions on respectful framing). Chapter 1/2 currently undersell this; a panel member reading only the front matter would not know the positive-conduct cases exist at all.
2. **Appendix list, front matter vs. back matter.** Covered above — two different, both-wrong lists of appendices exist in the same document.
3. **Sprint schedule vs. actual calendar date.** Covered above.

### Repetitive content
- None found that needs trimming. The document is lean; if anything it under-explains (missing abstract/ToC) rather than over-explains.

### Technical inaccuracies (checked against the real code)
None found in Chapter 3 as it now stands. Everything I checked lines up with the actual repository: FastAPI/Jinja2 stack, TF-IDF retrieval over `law_chunks.json`, the scikit-learn intent classifier now named correctly, the 20-case game module, and the "hand-rolled placeholder being replaced by a trained model" framing in 3.4.3 all match what is actually running.

### Sections requiring new/updated citations
- None identified as missing. If real WER/SUS results end up compared against other Taglish or Filipino ASR benchmarks in the eventual Chapter 4 discussion, that comparison will need its own citations at that time — not now.

### Sections requiring adviser approval before I touch them
- **Game scope wording in Chapter 1/2** (item 1 above): whether to explicitly add the positive-conduct half to the Scope and Conceptual Framework, or to leave Chapter 1/2 focused only on the offense-depicting cases and let Chapter 3 carry the full picture, is a **research-alignment / scope-correction** decision, not a writing fix. I have a recommendation (below) but this should not be changed silently.
- **Abstract and Acknowledgements content** — these need your and Jamie's actual voice/decisions (who to thank, how to summarize preliminary results), not something I should draft unprompted.
- **Appendix list** — needs your confirmation of what your actual appendices will be (I have a reasonable guess below, but this is your call, possibly your adviser's).

---

## B. CHANGE MATRIX

| Section | Current Issue | Recommended Change | Reason | Priority |
|---|---|---|---|---|
| Table of Contents | Entirely unedited CISTM template headings ("Fonts," "SI Units," "Equations," etc.) that don't match any real heading in the body | Regenerate the ToC from the actual Chapter 1–5 headings and update all page numbers | Writing improvement / document hygiene — a panel member will notice immediately | HIGH |
| Abstract | Literal placeholder instructions, no actual content | Draft a real 1–2 page abstract once Chapter 4 has at least preliminary/expected content to summarize, or a proposal-appropriate summary now (see Ch.5 formatting rule #4: proposals may include "Preliminary Results" instead) | Requirement — a thesis/proposal cannot be defended without an abstract | HIGH |
| Acknowledgements | Only the generic CISTM template thank-you remains | Replace with your and Jamie's actual acknowledgements | Requirement | HIGH |
| Appendices (back matter) | Lists "ICP-OES and AAS analysis," "Journal paper," other chemistry/unrelated template content; contradicts front-matter ToC's own (also wrong) appendix list | Replace with the real appendices this project needs — likely: source code/repo link, sample evaluation transcripts, the SUS questionnaire instrument, any consent/recommendation letters, and the Bionote that's already there | Technical correction / document hygiene | HIGH |
| Table 3.1, Sprint 9 row | Still marked "In Progress (current sprint)" though that date range has passed | Update status to "Completed," and add or extend a row/note covering the actual Sept 5–16 gap before the defense | Writing improvement (keep the schedule honest and current) | MEDIUM |
| Chapter 1 Scope / Chapter 2 Conceptual Framework | Describes the game only as "storyboards depicting offenses," omitting the 10 positive-conduct cases that Chapter 3 treats as central to the design | Recommend adding one clause to the Scope and Conceptual Framework acknowledging the game presents both offense and positive-conduct cases (10 + 10) | Research alignment / scope correction — needs your (and possibly your adviser's) sign-off since it touches how the "at least ten storyboards" objective language reads | HIGH — but **requires adviser approval**, not a silent fix |
| 3.3.2 / 3.3.3 (already fixed this session) | Previously `[INFORMATION NEEDED]`, now filled with Whisper-small/Hugging Face/scikit-learn and the 600-utterance/8–15-speaker corpus plan | No further action — already aligned with the real system | — | Resolved |
| 3.4.3 case-readiness statement (already fixed this session) | Previously said 2 of 20 cases ready | Already corrected to reflect all 20 ready | — | Resolved |
| Chapter 4 tables | All `[RESULTS PENDING]` | No action now — correctly honest for a proposal defense; revisit after STT/NLP modules are built and evaluated | Do not fabricate | LOW (by design, not a defect) |

---

## C. CONSISTENCY CHECK

| Element | Current Version | Recommended Version | Sections Affected |
|---|---|---|---|
| Title | "Integration of Taglish Speech-to-Text and an Applied Legal Consequence Game to an NLP-Based Chatbot Support System for Children in Conflict with the Law" | Consistent everywhere it appears (title page, running references) — no change needed | Title page, throughout |
| Target users | CICL, reached via partner institution (LSWDO/Bahay Pag-asa) plus IT experts | Consistent across Ch.1 Significance, Ch.3 3.1.2 Respondents, Ch.4 Table 4.1 | Ch.1, Ch.3, Ch.4 |
| Main problem | Existing Romilla et al. (2023) chatbot is text-only and dialogue-only, creating a language/modality barrier and an engagement ceiling | Consistent across Background, SOP, and Objectives | Ch.1 |
| General objective | Integrate Taglish STT + applied legal consequence game into the existing chatbot | Consistent | Ch.1 |
| Specific objectives (5, = 5 SOPs) | STT module, enhanced intent recognition, legal consequence game, performance evaluation, usability evaluation | Consistent 1:1 mapping maintained throughout Ch.1, Ch.2 (RRL sub-sections), Ch.3 (3.4.1–3.4.5) | Ch.1, Ch.2, Ch.3 |
| Core system features | Chat interface (Gemini-grounded RAG) + case-review booth game | Consistent with the actual running system | Ch.3 |
| AI/NLP component | Ch.1/2/3 describe "enhanced NLP intent recognition" via a to-be-trained library-based classifier | Now correctly named in 3.3.2 as scikit-learn (TF-IDF + LogisticRegression), replacing the hand-rolled placeholder — already aligned | Ch.3 |
| Speech-to-text component | Whisper-small, fine-tuned via Hugging Face, evaluated by WER | Consistent between Ch.1 (background), Ch.2 (RRL), Ch.3 (3.3.2, 3.4.1) | Ch.1, Ch.2, Ch.3 |
| Taglish component | Code-switched Tagalog-English, target of both STT and intent recognition | Consistent | Ch.1, Ch.2, Ch.3 |
| Legal consequence game | **Inconsistent**: Ch.1/2 say "at least ten storyboards depicting offenses"; Ch.3 says 20 total (10 offense + 10 positive-conduct) | Recommend aligning Ch.1/2 to acknowledge the full 20-case design (pending your approval — see Change Matrix) | Ch.1, Ch.2 vs. Ch.3 |
| Knowledge/legal source | RA 9344 as amended by RA 10630, plus Revised IRR | Consistent everywhere, including the actual 214-chunk retrieval base built from these exact three sources | Ch.1, Ch.2, Ch.3 |
| Methodology | Agile/Scrum, 3 increments (STT, NLP, game) | Consistent; Table 3.1 sprint table just needs a status/date refresh (see Change Matrix) | Ch.3 |
| Evaluation | WER + intent accuracy (Obj. 4), SUS with benchmark of 68 (Obj. 5) | Consistent across Ch.1, Ch.2 (RRL sub-section 5), Ch.3 (3.4.4–3.4.5), Ch.4 (tables) | Ch.1, Ch.2, Ch.3, Ch.4 |
| Scope | STT (Taglish/Tagalog/English) + game (≥10 storyboards) + SUS evaluation | Same "storyboards depicting offenses only" undercount as above | Ch.1 |
| Limitations | STT limited to Tagalog-English; game is educational, not legal advice; no recidivism measurement | Consistent, and already aligned with your Rule 4 (no overclaiming, not a substitute for lawyers/social workers/courts) — no change needed | Ch.1 |

---

## What I did NOT do

Per your instruction, I have not rewritten any section yet. The two items already corrected (3.3.2/3.3.3 info-needed gaps, and the case-readiness count in 3.4.3) were done in an earlier session before this review request and are noted above as resolved, not as new edits.

## Recommended next step

Tell me which of the HIGH-priority items to act on first. My suggestion, in order: (1) rebuild the Table of Contents and fix the appendix list — pure mechanical fixes, no judgment calls, safe to do immediately; (2) decide, with your adviser if needed, how to handle the Ch.1/2 vs. Ch.3 game-scope mismatch; (3) draft the Abstract and Acknowledgements once you tell me what you and Jamie want said (I can draft a first pass for you to edit, but the acknowledgements especially should reflect your actual voice); (4) refresh the Sprint 9 status and the Sept 4–16 gap in Table 3.1.
