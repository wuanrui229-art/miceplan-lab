# MICEPlan-Lab Interactive Author Review Session

- Reviewer: Wendy
- Review method: one strictly equivalent task group per chat turn; tasks are grouped
  only when Chinese text, English text, expected outcome, and non-scene-specific intent
  requirements are identical
- Assistant role: present the frozen task fields, explain the expected action in plain
  language, and record the author's response without changing it
- Model outputs visible during review: no
- Started: 2026-07-21
- Status: COMPLETE
- Progress: 90/90 tasks; 67/67 review groups

## Response mapping

- `通过`: Decision=PASS, CN/EN Equivalent=YES, Request Reasonable=YES
- `翻译问题`: Decision=FAIL, CN/EN Equivalent=NO; record the author's note
- `逻辑问题`: Decision=FAIL, Request Reasonable=NO; record the author's note
- `都有问题`: Decision=FAIL, CN/EN Equivalent=NO, Request Reasonable=NO
- `不确定`: remain PENDING and revisit with additional scene/context evidence

## Decisions

### Group 1 — task-0001, task-0002, task-0003, task-0007

- Author response: 通过
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: none

### Group 2 — task-0004

- Author response: 通过
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: none

### Group 3 — task-0005, task-0010, task-0011, task-0015

- Author response: 逻辑问题（确认）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The standalone simulated user utterance says only “this layout edit,” so
  the requested operation and target are missing. It also explicitly states that the
  scale is unavailable, which leaks the intended reason to defer. Revise to an
  operation-specific grid request while keeping scale/unit absent from the visible
  scene; then repeat author review before formal calls.

### Group 4 — task-0006, task-0008

- Author response: 逻辑问题（确认）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: “Close to” has no distance threshold and “the same row” does not
  identify a row. The preference is not operationally measurable and can confound the
  overlap-stress interpretation. Revise using a scene-supported measurable relation,
  then repeat author review and machine validation.

### Group 5 — task-0009

- Author response: 同意建议结论
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: “Close to” has no distance threshold and “the main aisle or entrance”
  does not identify one protected object. The task does not operationally distinguish
  proximity from occupation of a protected region. Revise using a scene-supported,
  measurable relation and rerun review and machine validation.

### Group 6 — task-0012

- Author response: 同意建议结论（after discussing the possible “shift outward” interpretation）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: E104 is already an available 4x3 standard booth. The witness removes it
  and adds an identical standard booth at the same coordinates, so the net spatial
  layout is unchanged. “In the released area” fixes the footprint while “outermost”
  suggests displacement, but no direction or distance is specified and the gold answer
  contains no displacement. Redesign to produce a meaningful, measurable net edit and
  rerun review and machine validation.

### Group 7 — task-0013

- Author response: 同意建议结论
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: F104 is already an available 4x3 standard booth and the witness replaces
  it with an identical booth at the same coordinates, so there is no meaningful net
  spatial change. “Close to the same row” additionally lacks a target row and distance
  definition. Redesign and revalidate before formal calls.

### Group 8 — task-0014

- Author response: 同意建议结论
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: G104 is already an available 4x3 standard booth and the witness replaces
  it with an identical booth at the same coordinates, so the net spatial layout is
  unchanged. The added “main aisle or entrance” preference has neither a unique
  protected target nor a distance definition. Redesign and revalidate before formal
  calls.

### Group 9 — task-0016

- Author response: 同意建议结论
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: A103 exists, is available, and can be moved. The valid witness produces
  a real displacement from (15, 2) to a feasible eastern location at (35, 10).
  “Open east area” permits multiple valid coordinates, so evaluation must accept
  any operation satisfying the east-zone intent and deterministic constraints rather
  than requiring exact coordinate equality with the witness.

### Group 10 — task-0017

- Author response: 同意建议结论
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: C103 exists, is available, and is genuinely moved from (15, 2) to a
  feasible eastern location at (37, 7). The task permits multiple compliant eastern
  coordinates, so evaluation should test the east-zone intent and deterministic
  constraints rather than exact equality with the witness coordinates.

### Group 11 — task-0018

- Author response: 同意建议结论
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: D103 exists and is available. The witness moves it from (15, 2) to a
  feasible eastern location at (43, 7), while the invalid probe at (49, 35) is clearly
  beyond the venue boundary of x <= 48 and y <= 34. “Outermost” is treated as a soft
  preference rather than an exact-coordinate requirement.

### Group 12 — task-0019

- Author response: 同意建议结论
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: The valid witness moves available booth E103 while preserving sold and
  locked booths. The invalid probe instead moves locked booth E102 and is therefore a
  clear LOCKED_MUTATION case. Reorganizing the row is optional, so a witness that only
  moves E103 remains consistent with the request.

### Group 13 — task-0020, task-0026

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The scene genuinely contains two entrances and multiple possible nearby
  booths, so DEFER is appropriate. However, the visible utterance explicitly says
  that neither entrance nor target is numbered, leaking the intended ambiguity and
  expected decision. “Adjust” also omits the desired change. Rewrite as a natural
  underspecified user request, preserve the hidden-label context, then repeat author
  review and machine validation. Task-0026 has the same bilingual text, masks,
  operation family, outcome, stress class, and intent requirements as task-0020, so
  the confirmed group decision applies to both scenes.

### Group 14 — task-0021

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: A103 is available and the witness moves it from (15, 2) to a feasible
  eastern location at (35, 10). The invalid probe at (41, 31) is clearly outside the
  40 x 30 venue boundary. “Outermost” remains a soft preference rather than a unique
  coordinate requirement.

### Group 15 — task-0022

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: G103 exists, is available, and is genuinely moved from (15, 2) to a
  feasible eastern location at (45, 7). The task is a clear feasible control and the
  evaluator should accept any compliant eastern destination rather than only the
  witness coordinate.

### Group 16 — task-0023

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The invalid probe at (21, 2) clearly overlaps H104, so the geometric
  stress case is valid. However, “close to” has no distance threshold, “the same row”
  lacks an operational definition, and neither the witness nor intent requirements
  encode the preference. Replace it with a measurable alignment and clearance
  condition, then repeat review and validation.

### Group 17 — task-0024

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: C103 is available and the witness moves only C103 to a feasible eastern
  location. The invalid probe instead moves locked booth C102, producing a clear
  LOCKED_MUTATION. Row reorganization is optional, so the single-move witness remains
  consistent with the request.

### Group 18 — task-0025

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The utterance does not identify a booth, movement direction, or concrete
  edit, while explicitly stating that scale and unit are unavailable. This leaks the
  intended reason for DEFER instead of testing whether the model detects missing
  evidence. Rewrite as a target-specific one-grid movement request while keeping the
  scale and unit absent from the visible scene, then repeat review and validation.

### Group 19 — task-0027

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: E104 is an available booth at (21, 2). The witness removes E104 and then
  genuinely moves E103 from (15, 2) into that released footprint. This produces a
  meaningful final-layout change, with explicit targets and operation order.

### Group 20 — task-0028

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: Removing F104 and moving F103 into its released footprint is a meaningful
  edit, and the boundary probe itself is valid. However, the equal-sized released
  footprint fixes the destination at (21, 2), leaving no “outermost” choice. If
  “outermost” refers to the venue, it conflicts with the released-area requirement.
  Remove or operationally redefine the preference, then repeat validation and review.

### Group 21 — task-0029

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The overlap probe is valid, but removing G104 fixes the equal-sized
  destination for G103 at the released footprint (21, 2). “Close to other booths in
  the same row” adds neither a measurable distance nor a meaningful placement choice,
  and is not encoded by the witness. Remove the redundant preference and revalidate.

### Group 22 — task-0030

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The protected-polygon probe correctly places H103 over a fixed column.
  However, the released equal-sized footprint fixes the valid destination at (21, 2),
  while “close to the main aisle or entrance” has no distance threshold, no unique
  protected target, and is not verified by the witness. Remove the preference and
  repeat review and validation.

### Group 23 — task-0031

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: B103 exists, is available, and changes meaningfully from 4 x 3 m to
  3 x 3 m. The witness modifies only the requested booth and remains geometrically
  feasible. The bilingual dimensions and units are equivalent.

### Group 24 — task-0032

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: C103 exists, is available, and changes meaningfully from 4 x 3 m to
  3 x 3 m. The witness resizes only the requested target and remains within all
  deterministic spatial constraints. The bilingual request is equivalent.

### Group 25 — task-0033

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The oversized-width boundary probe is valid, but RESIZE_BOOTH does not
  change position. “Use the outermost available position” therefore requires an
  unrequested movement and is ignored by the witness and intent requirements. Remove
  the positional sentence, then repeat review and validation.

### Group 26 — task-0034

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: E103 is available and changes from 4 x 3 m to 3 x 3 m. Row
  reorganization is optional, so the minimal witness that resizes only E103 satisfies
  the request. The invalid probe resizes locked booth E102 and is correctly classified
  as LOCKED_MUTATION.

### Group 27 — task-0035

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: DEFER is appropriate because the entrance, booth, and target dimensions
  are underspecified. However, the utterance explicitly says that the entrance and
  target are not numbered, leaking the intended ambiguity, while “adjust” does not
  reveal that resizing is intended. Rewrite as a natural resizing request whose target
  remains ambiguous under the hidden-label context, then repeat review and validation.

### Group 28 — task-0036

- Author response: 同意建议结论（“OK”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: B103 is available and is validly resized from 4 x 3 m to 3 x 3 m.
  Reorganizing the row is optional, so the minimal witness is acceptable. The invalid
  probe instead resizes locked booth B102 and correctly exercises LOCKED_MUTATION.

### Group 29 — task-0037

- Author response: 同意建议结论（“OK”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: G103 exists, is available, and changes meaningfully from 4 x 3 m to
  3 x 3 m. The witness modifies only the requested booth and satisfies all
  deterministic spatial constraints. The bilingual request is equivalent.

### Group 30 — task-0038

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: RESIZE_BOOTH cannot satisfy the positional “close to the same row” clause,
  which is also unmeasurable. More importantly, executing the 54 m-width invalid probe
  produces BOUNDARY, OVERLAP, and PROTECTED_POLYGON simultaneously, although the gold
  labels it as an OVERLAP probe. Replace it with a single-fault overlap seed that stays
  inside the hall and avoids protected polygons, then repeat validation and review.

### Group 31 — task-0039

- Author response: 同意建议结论（“OK”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: The valid witness resizes only available booth C103 and passes all rules.
  The invalid probe resizes locked booth C102 and, when executed, triggers only
  LOCKED_MUTATION. This is a clean single-fault probe, and row reorganization remains
  optional rather than required.

### Group 32 — task-0040, task-0041

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The utterance identifies neither a target booth nor the resize dimension
  and direction, while explicitly stating that grid scale and unit are unavailable.
  This leaks the intended reason for DEFER. Rewrite as a target-specific one-grid
  resize request while keeping scale and unit absent from the scene, then repeat
  validation and review. Task-0041 has the same bilingual text, masks, operation
  family, outcome, stress class, and intent requirements as task-0040, so the
  confirmed group decision applies to both scenes.

### Group 33 — task-0042

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: The witness removes available booth E104, moves E103 from (15, 2) into
  the released footprint at (21, 2), and resizes E103 from 4 x 3 m to 3 x 3 m.
  Executing the witness returns PASS, and each operation maps directly to the bilingual
  request.

### Group 34 — task-0043

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The released footprint fixes the move destination, so “outermost” is
  meaningless or conflicting and is ignored by the witness. In addition, executing
  the 92 m-width invalid probe triggers BOUNDARY, OVERLAP, and PROTECTED_POLYGON
  simultaneously despite being labelled as a BOUNDARY probe. Remove the preference
  and construct a true single-fault boundary probe before revalidation and review.

### Group 35 — task-0044

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The released footprint fixes the destination, while “close to the same
  row” has no measurable distance and no additional placement choice. Executing the
  50 m-width invalid probe triggers BOUNDARY, OVERLAP, and PROTECTED_POLYGON together,
  despite being labelled as an OVERLAP probe. Remove the preference and construct a
  single-fault overlap seed before revalidation and review.

### Group 36 — task-0045

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The released footprint fixes the destination, while “close to the main
  aisle or entrance” lacks a distance threshold and unique reference. The 54 x 36 m
  invalid resize probe triggers BOUNDARY, OVERLAP, and PROTECTED_POLYGON together,
  although it is labelled as a PROTECTED_POLYGON probe. Remove the preference and
  build a single-fault protected-region seed before revalidation and review.

### Group 37 — task-0046

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: A103 exists and is available. The witness removes only A103 and returns
  PASS under the deterministic oracle. The bilingual request is explicit and
  equivalent.

### Group 38 — task-0047

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: C103 exists and is available. The witness removes only C103, leaves
  protected statuses unchanged, and returns PASS. The bilingual request is explicit
  and equivalent.

### Group 39 — task-0048

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: D103 is available and the witness removes only D103, returning PASS. The
  invalid probe instead removes locked booth D102 and, when executed, triggers only
  LOCKED_MUTATION. Row reorganization is optional, so the minimal deletion is valid.

### Group 40 — task-0049, task-0054, task-0056, task-0059

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: Although an ambiguous target warrants DEFER, “adjust” does not express the
  intended REMOVE_BOOTH operation, and the visible utterance explicitly states that
  the entrance and target are not numbered. Rewrite as a natural deletion request
  whose candidate target remains ambiguous under the hidden-label context, then repeat
  validation and review. Tasks 0054, 0056, and 0059 have identical bilingual text,
  masks, operation family, outcome, stress class, and intent requirements, so the
  confirmed decision applies to all four scenes.

### Group 41 — task-0050, task-0055, task-0060

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: A one-grid-unit requirement has no meaningful relation to the discrete
  REMOVE_BOOTH operation. The utterance also omits the target and explicitly reveals
  that scale and unit are unavailable. Replace this with deletion-specific missing
  evidence, such as an absent identifying attribute, then repeat validation and review.
  Tasks 0055 and 0060 have identical bilingual text, masks, operation family, outcome,
  stress class, and intent requirements, so the confirmed decision applies to all
  three scenes.

### Group 42 — task-0051

- Author response: 同意建议结论（“OK”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: A103 is available and the valid witness removes only A103, returning PASS.
  The invalid probe instead removes locked booth A102 and triggers only
  LOCKED_MUTATION. Row reorganization is optional, so the minimal deletion remains
  consistent with the request.

### Group 43 — task-0052

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: G103 exists and is available. The witness removes only G103, returns PASS,
  and leaves sold, locked, and reserved booths unchanged. The bilingual request is
  explicit and equivalent.

### Group 44 — task-0053

- Author response: 同意建议结论（“OK”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: H103 is available and the valid witness removes only H103, returning PASS.
  The invalid probe instead removes locked booth H102 and triggers only
  LOCKED_MUTATION. Row reorganization is optional, so the minimal deletion remains
  consistent with the request.

### Group 45 — task-0057

- Author response: 同意建议结论（“ok”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: The witness removes available booth E103 and genuinely moves E104 from
  (21, 2) into the released footprint at (15, 2). It returns PASS and creates a
  meaningful final-layout change. The bilingual targets and sequence are explicit.

### Group 46 — task-0058

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: The bilingual request and valid witness are reasonable, and the witness
  returns PASS. However, the invalid probe removes locked F102 instead of F103 and then
  moves F104 onto the still-occupied F103 footprint. It therefore triggers both
  LOCKED_MUTATION and OVERLAP despite being labelled as a locked-only probe. Replace
  it with a single-fault locked mutation and repeat validation and review.

### Group 47 — task-0061

- Author response: 同意建议结论（“OK”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: B103 is an available 4 x 3 m booth. Splitting it into two 2 x 3 m booths
  exactly occupies the original footprint, and the witness returns PASS. Counts,
  dimensions, units, and target are equivalent across languages.

### Group 48 — task-0062

- Author response: 同意建议结论（“OK”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: C103 is an available 4 x 3 m booth. The witness splits it into two
  2 x 3 m booths within the original footprint and returns PASS. Counts, dimensions,
  units, and target are equivalent across languages.

### Group 49 — task-0063

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The invalid probe is a clean BOUNDARY-only case. However, two 2 x 3 m
  child booths exactly fill D103's original 4 x 3 m footprint, and SPLIT_BOOTH does not
  relocate the target. “Outermost” therefore has no placement choice and is ignored by
  the witness. Remove the positional preference and repeat review and validation.

### Group 50 — task-0064

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: The bilingual request and valid witness are reasonable, and the witness
  returns PASS. However, the invalid probe splits locked E102 and places the children
  on the still-occupied E103 footprint, triggering both LOCKED_MUTATION and OVERLAP.
  Execute the locked split in E102's own footprint to create a single-fault probe, then
  repeat validation and review.

### Group 51 — task-0065

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: An ambiguous target can justify DEFER, but “adjust” does not express the
  intended SPLIT_BOOTH operation, and neither child count nor dimensions are given.
  The utterance also explicitly reveals that entrance and target labels are absent.
  Rewrite as a natural split request whose target remains ambiguous under the hidden
  labels, then repeat validation and review.

### Group 52 — task-0066

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The invalid probe is a clean OVERLAP-only case. However, two 2 x 3 m
  children exactly fill B103's original footprint, leaving no placement choice, while
  “close to” and “the same row” lack measurable definitions and are not encoded by the
  witness. Remove the preference and repeat validation and review.

### Group 53 — task-0067

- Author response: 同意建议结论（“OK”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: G103 is an available 4 x 3 m booth. The witness splits it into two
  2 x 3 m booths within the original footprint and returns PASS. Counts, dimensions,
  units, and target are equivalent across languages.

### Group 54 — task-0068

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The witness passes and the invalid probe is a clean OVERLAP-only case.
  However, two 2 x 3 m children exactly fill H103's original footprint, leaving no
  placement choice, while “close to” and “the same row” lack measurable definitions.
  Remove the redundant preference and repeat validation and review.

### Group 55 — task-0069

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: The bilingual request and witness are reasonable, and the witness returns
  PASS. However, the invalid probe splits locked C102 and places the child booths on
  the still-occupied C103 footprint, triggering both LOCKED_MUTATION and OVERLAP.
  Split C102 within its own footprint to create a locked-only fault, then repeat
  validation and review.

### Group 56 — task-0070, task-0071

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The utterance identifies neither the split target nor child count,
  dimensions, or orientation, while explicitly stating that grid scale and unit are
  unavailable. This leaks the intended reason for DEFER. Rewrite as a target-specific
  grid-dependent split request and keep the scale absent from the visible scene, then
  repeat validation and review. Task-0071 has the same bilingual text, masks,
  operation family, outcome, stress class, and intent requirements as task-0070, so
  the confirmed decision applies to both scenes.

### Group 57 — task-0072

- Author response: 同意建议结论（“OK”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: The witness removes available booth E104, splits editable 4 x 3 m booth
  E103 into two 2 x 3 m children, and places them in the released (21, 2) footprint.
  It returns PASS, creates a meaningful final layout, and directly matches the
  bilingual request.

### Group 58 — task-0073

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The witness passes and the invalid probe is a clean OVERLAP-only case.
  However, the released footprint fixes the destination and the two child booths fill
  it exactly. “Close to the same row” adds no placement choice or measurable distance
  and is not encoded by the witness. Remove the preference and repeat validation and
  review.

### Group 59 — task-0074

- Author response: 同意建议结论（“ok”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The witness passes and the invalid probe is a clean
  PROTECTED_POLYGON-only case. However, the released footprint fixes the destination,
  while “close to the main aisle or entrance” has no threshold or unique reference and
  is not verified by the witness. Remove the preference and repeat validation and
  review.

### Group 60 — task-0075

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The witness passes and the invalid probe is a clean
  PROTECTED_POLYGON-only case. However, the released footprint fixes the destination,
  while “close to the main aisle or entrance” has no threshold or unique reference and
  is not verified by the witness. Remove the preference and repeat validation and
  review.

### Group 61 — task-0076, task-0077, task-0082

- Author response: 同意建议结论（“OK”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: These tasks have identical bilingual text, masks, operation family,
  outcome, stress class, and intent requirements across three scenes. Each witness
  reserves a 2 x 5 m aisle in a feasible southern open area and returns PASS. Any
  compliant southern coordinate should be accepted rather than only the witness
  coordinate.

### Group 62 — task-0078, task-0083

- Author response: 同意建议结论（“OK”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: The two tasks have identical review signatures across different scenes.
  Each witness reserves a 2 x 5 m aisle near the southern outer boundary and returns
  PASS. Each invalid probe triggers only BOUNDARY. “Outermost” is treated as a soft
  preference rather than an exact-coordinate requirement.

### Group 63 — task-0079, task-0081, task-0084

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: These three tasks share an identical review signature across scenes. Their
  witnesses pass and their invalid probes are clean PROTECTED_POLYGON-only cases.
  However, “close to the main aisle or entrance” has no distance threshold or unique
  reference and is not encoded by the intent requirements. Remove it or replace it
  with a measurable named-reference distance, then repeat validation and review.

### Group 64 — task-0080, task-0085, task-0086, task-0090

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The scenes genuinely contain multiple entrances, so DEFER is appropriate.
  However, all four visible utterances explicitly state that the entrance is not
  identified, leaking the intended ambiguity. Rewrite as a natural dimensioned aisle
  request beside “the entrance,” keep entrance labels hidden, and let the model detect
  the ambiguity from the scene before repeating validation and review.

### Group 65 — task-0087

- Author response: 同意建议结论（“OK”）
- Decision: PASS
- CN/EN Equivalent: YES
- Request Reasonable: YES
- Notes: E104 is an available 4 x 3 m booth. The witness removes it and reserves a
  same-size 4 x 3 m aisle in the released (21, 2) footprint, returning PASS and
  producing a meaningful booth-to-aisle layout change. The bilingual request is
  equivalent.

### Group 66 — task-0088

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The released footprint fixes the aisle location, while “close to the same
  row” is not measurable or natural for an aisle. The invalid probe triggers only
  OVERLAP geometrically, but it adds an unrequested MOVE_BOOTH operation; its intent
  signature is therefore false. Remove the preference and construct a semantically
  faithful overlap-only probe before revalidation and review.

### Group 67 — task-0089

- Author response: 同意建议结论（“OK”）
- Decision: FAIL
- CN/EN Equivalent: YES
- Request Reasonable: NO
- Notes: The released footprint fixes the aisle anchor and “close to the main aisle
  or entrance” is unmeasurable and ambiguous. The invalid probe triggers only
  PROTECTED_POLYGON geometrically, but places the aisle at (15, 2) instead of the
  required released anchor (21, 2), so its intent signature is false. Remove the
  preference and construct a semantically faithful protected-region task before
  revalidation and review.
