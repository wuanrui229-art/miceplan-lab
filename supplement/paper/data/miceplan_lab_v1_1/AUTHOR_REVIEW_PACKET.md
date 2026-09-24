# MICEPlan-Lab v1.1 Blinded Surface-Form Review Packet

This packet contains no model outputs. Review each bilingual task against the
scene, intended operation family, context mask, and hidden witness/probe design.
Mark PASS or record a correction before formal model calls. This is internal
benchmark quality control, not practitioner or domain-expert validation.

## task-0001 — ADD_BOOTH / C1 / FEASIBLE_CONTROL

- Scene: `dev-scene-02`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在东侧开放区域新增 1 个 3×3 米标准展位。
- English: Add 1 standard booth of 3 x 3 m in the open east area.
- Intent requirements: `{"count": 1, "goal_zone": "east", "height": 3, "required_operation_types": ["ADD_BOOTH"], "width": 3}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0002 — ADD_BOOTH / C1 / MISSING_EVIDENCE

- Scene: `test-scene-03`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": true, "hide_unit": true}`
- Chinese: 在东侧开放区域新增一个占 1×1 网格单元的标准展位。
- English: Add one standard booth occupying 1 x 1 grid cell in the open east area.
- Intent requirements: `{"required_operation_types": ["ADD_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0003 — ADD_BOOTH / C1 / FEASIBLE_CONTROL

- Scene: `test-scene-04`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在东侧开放区域新增 1 个 3×3 米标准展位。
- English: Add 1 standard booth of 3 x 3 m in the open east area.
- Intent requirements: `{"count": 1, "goal_zone": "east", "height": 3, "required_operation_types": ["ADD_BOOTH"], "width": 3}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0004 — ADD_BOOTH / C1 / BOUNDARY

- Scene: `test-scene-05`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在东侧开放区域新增 1 个 3×3 米标准展位。
- English: Add 1 standard booth of 3 x 3 m in the open east area.
- Intent requirements: `{"count": 1, "goal_zone": "east", "height": 3, "required_operation_types": ["ADD_BOOTH"], "width": 3}`
- Witness present: `True`
- Probe rules: `["BOUNDARY"]`
- Review decision: **PASS**
- Review notes:

## task-0005 — ADD_BOOTH / C1 / MISSING_EVIDENCE

- Scene: `test-scene-06`; booths=12; boundary vertices=6
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": true, "hide_unit": true}`
- Chinese: 在东侧开放区域新增一个占 1×1 网格单元的标准展位。
- English: Add one standard booth occupying 1 x 1 grid cell in the open east area.
- Intent requirements: `{"required_operation_types": ["ADD_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0006 — ADD_BOOTH / C2 / OVERLAP

- Scene: `dev-scene-02`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在东侧开放区域新增 1 个 3×3 米标准展位。
- English: Add 1 standard booth of 3 x 3 m in the open east area.
- Intent requirements: `{"count": 1, "goal_zone": "east", "height": 3, "required_operation_types": ["ADD_BOOTH"], "width": 3}`
- Witness present: `True`
- Probe rules: `["OVERLAP"]`
- Review decision: **PASS**
- Review notes:

## task-0007 — ADD_BOOTH / C2 / FEASIBLE_CONTROL

- Scene: `test-scene-07`; booths=12; boundary vertices=8
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在东侧开放区域新增 1 个 3×3 米标准展位。
- English: Add 1 standard booth of 3 x 3 m in the open east area.
- Intent requirements: `{"count": 1, "goal_zone": "east", "height": 3, "required_operation_types": ["ADD_BOOTH"], "width": 3}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0008 — ADD_BOOTH / C2 / OVERLAP

- Scene: `test-scene-08`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在东侧开放区域新增 1 个 3×3 米标准展位。
- English: Add 1 standard booth of 3 x 3 m in the open east area.
- Intent requirements: `{"count": 1, "goal_zone": "east", "height": 3, "required_operation_types": ["ADD_BOOTH"], "width": 3}`
- Witness present: `True`
- Probe rules: `["OVERLAP"]`
- Review decision: **PASS**
- Review notes:

## task-0009 — ADD_BOOTH / C2 / PROTECTED_POLYGON

- Scene: `test-scene-03`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在东侧开放区域新增 1 个 3×3 米标准展位。
- English: Add 1 standard booth of 3 x 3 m in the open east area.
- Intent requirements: `{"count": 1, "goal_zone": "east", "height": 3, "required_operation_types": ["ADD_BOOTH"], "width": 3}`
- Witness present: `True`
- Probe rules: `["PROTECTED_POLYGON"]`
- Review decision: **PASS**
- Review notes:

## task-0010 — ADD_BOOTH / C2 / MISSING_EVIDENCE

- Scene: `test-scene-04`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": true, "hide_unit": true}`
- Chinese: 在东侧开放区域新增一个占 1×1 网格单元的标准展位。
- English: Add one standard booth occupying 1 x 1 grid cell in the open east area.
- Intent requirements: `{"required_operation_types": ["ADD_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0011 — ADD_BOOTH / C3 / MISSING_EVIDENCE

- Scene: `dev-scene-02`; booths=12; boundary vertices=6
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": true, "hide_unit": true}`
- Chinese: 在东侧开放区域新增一个占 1×1 网格单元的标准展位。
- English: Add one standard booth occupying 1 x 1 grid cell in the open east area.
- Intent requirements: `{"required_operation_types": ["ADD_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0012 — ADD_BOOTH / C3 / BOUNDARY

- Scene: `test-scene-05`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 E104，再在东侧开放区域新增一个 3×3 米标准展位。
- English: Remove E104, then add one 3 x 3 m standard booth in the open east area.
- Intent requirements: `{"count": 1, "goal_zone": "east", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "ADD_BOOTH"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-5-booth-04"]}, "width": 3}`
- Witness present: `True`
- Probe rules: `["BOUNDARY"]`
- Review decision: **PASS**
- Review notes:

## task-0013 — ADD_BOOTH / C3 / OVERLAP

- Scene: `test-scene-06`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 F104，再在东侧开放区域新增一个 3×3 米标准展位。
- English: Remove F104, then add one 3 x 3 m standard booth in the open east area.
- Intent requirements: `{"count": 1, "goal_zone": "east", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "ADD_BOOTH"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-6-booth-04"]}, "width": 3}`
- Witness present: `True`
- Probe rules: `["OVERLAP"]`
- Review decision: **PASS**
- Review notes:

## task-0014 — ADD_BOOTH / C3 / PROTECTED_POLYGON

- Scene: `test-scene-07`; booths=12; boundary vertices=8
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 G104，再在东侧开放区域新增一个 3×3 米标准展位。
- English: Remove G104, then add one 3 x 3 m standard booth in the open east area.
- Intent requirements: `{"count": 1, "goal_zone": "east", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "ADD_BOOTH"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-7-booth-04"]}, "width": 3}`
- Witness present: `True`
- Probe rules: `["PROTECTED_POLYGON"]`
- Review decision: **PASS**
- Review notes:

## task-0015 — ADD_BOOTH / C3 / MISSING_EVIDENCE

- Scene: `test-scene-08`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": true, "hide_unit": true}`
- Chinese: 在东侧开放区域新增一个占 1×1 网格单元的标准展位。
- English: Add one standard booth occupying 1 x 1 grid cell in the open east area.
- Intent requirements: `{"required_operation_types": ["ADD_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0016 — MOVE_BOOTH / C1 / FEASIBLE_CONTROL

- Scene: `dev-scene-01`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 A103 移到东侧开放区域。
- English: Move A103 to the open east area.
- Intent requirements: `{"goal_zone": "east", "required_operation_types": ["MOVE_BOOTH"], "required_target_ids": ["scene-1-booth-03"]}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0017 — MOVE_BOOTH / C1 / MISSING_EVIDENCE

- Scene: `test-scene-03`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": true, "hide_unit": true}`
- Chinese: 把 C103 向东移动一个网格单元。
- English: Move C103 one grid cell east.
- Intent requirements: `{"required_operation_types": ["MOVE_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0018 — MOVE_BOOTH / C1 / BOUNDARY

- Scene: `test-scene-04`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 D103 移到东侧开放区域。
- English: Move D103 to the open east area.
- Intent requirements: `{"goal_zone": "east", "required_operation_types": ["MOVE_BOOTH"], "required_target_ids": ["scene-4-booth-03"]}`
- Witness present: `True`
- Probe rules: `["BOUNDARY"]`
- Review decision: **PASS**
- Review notes:

## task-0019 — MOVE_BOOTH / C1 / PROTECTED_POLYGON

- Scene: `test-scene-05`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 E103 移到东侧开放区域。
- English: Move E103 to the open east area.
- Intent requirements: `{"goal_zone": "east", "required_operation_types": ["MOVE_BOOTH"], "required_target_ids": ["scene-5-booth-03"]}`
- Witness present: `True`
- Probe rules: `["PROTECTED_POLYGON"]`
- Review decision: **PASS**
- Review notes:

## task-0020 — MOVE_BOOTH / C1 / AMBIGUOUS_TARGET

- Scene: `test-scene-06`; booths=12; boundary vertices=6
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": true, "hide_scale": false, "hide_unit": false}`
- Chinese: 把入口旁边的一个展位移到东侧开放区域。
- English: Move a booth beside the entrance to the open east area.
- Intent requirements: `{"required_operation_types": ["MOVE_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0021 — MOVE_BOOTH / C2 / BOUNDARY

- Scene: `dev-scene-01`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 A103 移到东侧开放区域。
- English: Move A103 to the open east area.
- Intent requirements: `{"goal_zone": "east", "required_operation_types": ["MOVE_BOOTH"], "required_target_ids": ["scene-1-booth-03"]}`
- Witness present: `True`
- Probe rules: `["BOUNDARY"]`
- Review decision: **PASS**
- Review notes:

## task-0022 — MOVE_BOOTH / C2 / FEASIBLE_CONTROL

- Scene: `test-scene-07`; booths=12; boundary vertices=8
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 G103 移到东侧开放区域。
- English: Move G103 to the open east area.
- Intent requirements: `{"goal_zone": "east", "required_operation_types": ["MOVE_BOOTH"], "required_target_ids": ["scene-7-booth-03"]}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0023 — MOVE_BOOTH / C2 / OVERLAP

- Scene: `test-scene-08`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 H103 移到东侧开放区域。
- English: Move H103 to the open east area.
- Intent requirements: `{"goal_zone": "east", "required_operation_types": ["MOVE_BOOTH"], "required_target_ids": ["scene-8-booth-03"]}`
- Witness present: `True`
- Probe rules: `["OVERLAP"]`
- Review decision: **PASS**
- Review notes:

## task-0024 — MOVE_BOOTH / C2 / LOCKED_MUTATION

- Scene: `test-scene-03`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 C103 移到东侧开放区域。不得改动已售或锁定展位。
- English: Move C103 to the open east area. Do not modify sold or locked booths.
- Intent requirements: `{"goal_zone": "east", "required_operation_types": ["MOVE_BOOTH"], "required_target_ids": ["scene-3-booth-03"]}`
- Witness present: `True`
- Probe rules: `["LOCKED_MUTATION"]`
- Review decision: **PASS**
- Review notes:

## task-0025 — MOVE_BOOTH / C2 / MISSING_EVIDENCE

- Scene: `test-scene-04`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": true, "hide_unit": true}`
- Chinese: 把 D103 向东移动一个网格单元。
- English: Move D103 one grid cell east.
- Intent requirements: `{"required_operation_types": ["MOVE_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0026 — MOVE_BOOTH / C3 / AMBIGUOUS_TARGET

- Scene: `dev-scene-01`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": true, "hide_scale": false, "hide_unit": false}`
- Chinese: 把入口旁边的一个展位移到东侧开放区域。
- English: Move a booth beside the entrance to the open east area.
- Intent requirements: `{"required_operation_types": ["MOVE_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0027 — MOVE_BOOTH / C3 / FEASIBLE_CONTROL

- Scene: `test-scene-05`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 E104，再把 E103 移到东侧开放区域。
- English: Remove E104, then move E103 to the open east area.
- Intent requirements: `{"goal_zone": "east", "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH"], "required_target_ids": ["scene-5-booth-03"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-5-booth-04"]}}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0028 — MOVE_BOOTH / C3 / BOUNDARY

- Scene: `test-scene-06`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 F104，再把 F103 移到东侧开放区域。
- English: Remove F104, then move F103 to the open east area.
- Intent requirements: `{"goal_zone": "east", "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH"], "required_target_ids": ["scene-6-booth-03"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-6-booth-04"]}}`
- Witness present: `True`
- Probe rules: `["BOUNDARY"]`
- Review decision: **PASS**
- Review notes:

## task-0029 — MOVE_BOOTH / C3 / OVERLAP

- Scene: `test-scene-07`; booths=12; boundary vertices=8
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 G104，再把 G103 移到东侧开放区域。
- English: Remove G104, then move G103 to the open east area.
- Intent requirements: `{"goal_zone": "east", "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH"], "required_target_ids": ["scene-7-booth-03"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-7-booth-04"]}}`
- Witness present: `True`
- Probe rules: `["OVERLAP"]`
- Review decision: **PASS**
- Review notes:

## task-0030 — MOVE_BOOTH / C3 / PROTECTED_POLYGON

- Scene: `test-scene-08`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 H104，再把 H103 移到东侧开放区域。
- English: Remove H104, then move H103 to the open east area.
- Intent requirements: `{"goal_zone": "east", "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH"], "required_target_ids": ["scene-8-booth-03"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-8-booth-04"]}}`
- Witness present: `True`
- Probe rules: `["PROTECTED_POLYGON"]`
- Review decision: **PASS**
- Review notes:

## task-0031 — RESIZE_BOOTH / C1 / FEASIBLE_CONTROL

- Scene: `dev-scene-02`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 B103 调整为 3×3 米。
- English: Resize B103 to 3 x 3 m.
- Intent requirements: `{"height": 3, "required_operation_types": ["RESIZE_BOOTH"], "required_target_ids": ["scene-2-booth-03"], "width": 3}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0032 — RESIZE_BOOTH / C1 / MISSING_EVIDENCE

- Scene: `test-scene-03`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": true, "hide_unit": true}`
- Chinese: 把 C103 的宽度增加一个网格单元，高度保持不变。
- English: Increase the width of C103 by one grid cell and keep its height unchanged.
- Intent requirements: `{"required_operation_types": ["RESIZE_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0033 — RESIZE_BOOTH / C1 / BOUNDARY

- Scene: `test-scene-04`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 D107 调整为 3×3 米。
- English: Resize D107 to 3 x 3 m.
- Intent requirements: `{"height": 3, "required_operation_types": ["RESIZE_BOOTH"], "required_target_ids": ["scene-4-booth-07"], "width": 3}`
- Witness present: `True`
- Probe rules: `["BOUNDARY"]`
- Review decision: **PASS**
- Review notes:

## task-0034 — RESIZE_BOOTH / C1 / LOCKED_MUTATION

- Scene: `test-scene-05`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 E103 调整为 3×3 米。不得改动已售或锁定展位。
- English: Resize E103 to 3 x 3 m. Do not modify sold or locked booths.
- Intent requirements: `{"height": 3, "required_operation_types": ["RESIZE_BOOTH"], "required_target_ids": ["scene-5-booth-03"], "width": 3}`
- Witness present: `True`
- Probe rules: `["LOCKED_MUTATION"]`
- Review decision: **PASS**
- Review notes:

## task-0035 — RESIZE_BOOTH / C1 / AMBIGUOUS_TARGET

- Scene: `test-scene-06`; booths=12; boundary vertices=6
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": true, "hide_scale": false, "hide_unit": false}`
- Chinese: 把入口旁边的一个展位调整为 3×3 米。
- English: Resize a booth beside the entrance to 3 x 3 m.
- Intent requirements: `{"required_operation_types": ["RESIZE_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0036 — RESIZE_BOOTH / C2 / LOCKED_MUTATION

- Scene: `dev-scene-02`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 B103 调整为 3×3 米。不得改动已售或锁定展位。
- English: Resize B103 to 3 x 3 m. Do not modify sold or locked booths.
- Intent requirements: `{"height": 3, "required_operation_types": ["RESIZE_BOOTH"], "required_target_ids": ["scene-2-booth-03"], "width": 3}`
- Witness present: `True`
- Probe rules: `["LOCKED_MUTATION"]`
- Review decision: **PASS**
- Review notes:

## task-0037 — RESIZE_BOOTH / C2 / FEASIBLE_CONTROL

- Scene: `test-scene-07`; booths=12; boundary vertices=8
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 G103 调整为 3×3 米。
- English: Resize G103 to 3 x 3 m.
- Intent requirements: `{"height": 3, "required_operation_types": ["RESIZE_BOOTH"], "required_target_ids": ["scene-7-booth-03"], "width": 3}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0038 — RESIZE_BOOTH / C2 / OVERLAP

- Scene: `test-scene-08`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 H103 调整为 3×3 米。
- English: Resize H103 to 3 x 3 m.
- Intent requirements: `{"height": 3, "required_operation_types": ["RESIZE_BOOTH"], "required_target_ids": ["scene-8-booth-03"], "width": 3}`
- Witness present: `True`
- Probe rules: `["OVERLAP"]`
- Review decision: **PASS**
- Review notes:

## task-0039 — RESIZE_BOOTH / C2 / LOCKED_MUTATION

- Scene: `test-scene-03`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 C103 调整为 3×3 米。不得改动已售或锁定展位。
- English: Resize C103 to 3 x 3 m. Do not modify sold or locked booths.
- Intent requirements: `{"height": 3, "required_operation_types": ["RESIZE_BOOTH"], "required_target_ids": ["scene-3-booth-03"], "width": 3}`
- Witness present: `True`
- Probe rules: `["LOCKED_MUTATION"]`
- Review decision: **PASS**
- Review notes:

## task-0040 — RESIZE_BOOTH / C2 / MISSING_EVIDENCE

- Scene: `test-scene-04`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": true, "hide_unit": true}`
- Chinese: 把 D103 的宽度增加一个网格单元，高度保持不变。
- English: Increase the width of D103 by one grid cell and keep its height unchanged.
- Intent requirements: `{"required_operation_types": ["RESIZE_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0041 — RESIZE_BOOTH / C3 / MISSING_EVIDENCE

- Scene: `dev-scene-02`; booths=12; boundary vertices=6
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": true, "hide_unit": true}`
- Chinese: 把 B103 的宽度增加一个网格单元，高度保持不变。
- English: Increase the width of B103 by one grid cell and keep its height unchanged.
- Intent requirements: `{"required_operation_types": ["RESIZE_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0042 — RESIZE_BOOTH / C3 / FEASIBLE_CONTROL

- Scene: `test-scene-05`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 E104，再把 E103 移到东侧开放区域并调整为 3×3 米。
- English: Remove E104, then move E103 to the open east area and resize it to 3 x 3 m.
- Intent requirements: `{"goal_zone": "east", "goal_zone_operation_type": "MOVE_BOOTH", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH", "RESIZE_BOOTH"], "required_target_ids": ["scene-5-booth-03"], "required_targets_by_operation": {"MOVE_BOOTH": ["scene-5-booth-03"], "REMOVE_BOOTH": ["scene-5-booth-04"]}, "width": 3}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0043 — RESIZE_BOOTH / C3 / BOUNDARY

- Scene: `test-scene-06`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 F103，再把 F107 移到东侧开放区域并调整为 3×3 米。
- English: Remove F103, then move F107 to the open east area and resize it to 3 x 3 m.
- Intent requirements: `{"goal_zone": "east", "goal_zone_operation_type": "MOVE_BOOTH", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH", "RESIZE_BOOTH"], "required_target_ids": ["scene-6-booth-07"], "required_targets_by_operation": {"MOVE_BOOTH": ["scene-6-booth-07"], "REMOVE_BOOTH": ["scene-6-booth-03"]}, "width": 3}`
- Witness present: `True`
- Probe rules: `["BOUNDARY"]`
- Review decision: **PASS**
- Review notes:

## task-0044 — RESIZE_BOOTH / C3 / OVERLAP

- Scene: `test-scene-07`; booths=12; boundary vertices=8
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 G104，再把 G103 移到东侧开放区域并调整为 3×3 米。
- English: Remove G104, then move G103 to the open east area and resize it to 3 x 3 m.
- Intent requirements: `{"goal_zone": "east", "goal_zone_operation_type": "MOVE_BOOTH", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH", "RESIZE_BOOTH"], "required_target_ids": ["scene-7-booth-03"], "required_targets_by_operation": {"MOVE_BOOTH": ["scene-7-booth-03"], "REMOVE_BOOTH": ["scene-7-booth-04"]}, "width": 3}`
- Witness present: `True`
- Probe rules: `["OVERLAP"]`
- Review decision: **PASS**
- Review notes:

## task-0045 — RESIZE_BOOTH / C3 / LOCKED_MUTATION

- Scene: `test-scene-08`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 H104，再把 H103 移到东侧开放区域并调整为 3×3 米。不得改动已售或锁定展位。
- English: Remove H104, then move H103 to the open east area and resize it to 3 x 3 m. Do not modify sold or locked booths.
- Intent requirements: `{"goal_zone": "east", "goal_zone_operation_type": "MOVE_BOOTH", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH", "RESIZE_BOOTH"], "required_target_ids": ["scene-8-booth-03"], "required_targets_by_operation": {"MOVE_BOOTH": ["scene-8-booth-03"], "REMOVE_BOOTH": ["scene-8-booth-04"]}, "width": 3}`
- Witness present: `True`
- Probe rules: `["LOCKED_MUTATION"]`
- Review decision: **PASS**
- Review notes:

## task-0046 — REMOVE_BOOTH / C1 / FEASIBLE_CONTROL

- Scene: `dev-scene-01`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 删除可用展位 A103。
- English: Remove available booth A103.
- Intent requirements: `{"required_operation_types": ["REMOVE_BOOTH"], "required_target_ids": ["scene-1-booth-03"]}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0047 — REMOVE_BOOTH / C1 / FEASIBLE_CONTROL

- Scene: `test-scene-03`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 删除可用展位 C103。
- English: Remove available booth C103.
- Intent requirements: `{"required_operation_types": ["REMOVE_BOOTH"], "required_target_ids": ["scene-3-booth-03"]}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0048 — REMOVE_BOOTH / C1 / LOCKED_MUTATION

- Scene: `test-scene-04`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 删除可用展位 D103。不得改动已售或锁定展位。
- English: Remove available booth D103. Do not modify sold or locked booths.
- Intent requirements: `{"required_operation_types": ["REMOVE_BOOTH"], "required_target_ids": ["scene-4-booth-03"]}`
- Witness present: `True`
- Probe rules: `["LOCKED_MUTATION"]`
- Review decision: **PASS**
- Review notes:

## task-0049 — REMOVE_BOOTH / C1 / AMBIGUOUS_TARGET

- Scene: `test-scene-05`; booths=12; boundary vertices=6
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": true, "hide_scale": false, "hide_unit": false}`
- Chinese: 删除入口旁边的一个展位。
- English: Remove a booth beside the entrance.
- Intent requirements: `{"required_operation_types": ["REMOVE_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0050 — REMOVE_BOOTH / C1 / FEASIBLE_CONTROL

- Scene: `test-scene-06`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 删除可用展位 F103。
- English: Remove available booth F103.
- Intent requirements: `{"required_operation_types": ["REMOVE_BOOTH"], "required_target_ids": ["scene-6-booth-03"]}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0051 — REMOVE_BOOTH / C2 / LOCKED_MUTATION

- Scene: `dev-scene-01`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 删除可用展位 A103。不得改动已售或锁定展位。
- English: Remove available booth A103. Do not modify sold or locked booths.
- Intent requirements: `{"required_operation_types": ["REMOVE_BOOTH"], "required_target_ids": ["scene-1-booth-03"]}`
- Witness present: `True`
- Probe rules: `["LOCKED_MUTATION"]`
- Review decision: **PASS**
- Review notes:

## task-0052 — REMOVE_BOOTH / C2 / FEASIBLE_CONTROL

- Scene: `test-scene-07`; booths=12; boundary vertices=8
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 删除可用展位 G103。
- English: Remove available booth G103.
- Intent requirements: `{"required_operation_types": ["REMOVE_BOOTH"], "required_target_ids": ["scene-7-booth-03"]}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0053 — REMOVE_BOOTH / C2 / LOCKED_MUTATION

- Scene: `test-scene-08`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 删除可用展位 H103。不得改动已售或锁定展位。
- English: Remove available booth H103. Do not modify sold or locked booths.
- Intent requirements: `{"required_operation_types": ["REMOVE_BOOTH"], "required_target_ids": ["scene-8-booth-03"]}`
- Witness present: `True`
- Probe rules: `["LOCKED_MUTATION"]`
- Review decision: **PASS**
- Review notes:

## task-0054 — REMOVE_BOOTH / C2 / AMBIGUOUS_TARGET

- Scene: `test-scene-03`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": true, "hide_scale": false, "hide_unit": false}`
- Chinese: 删除入口旁边的一个展位。
- English: Remove a booth beside the entrance.
- Intent requirements: `{"required_operation_types": ["REMOVE_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0055 — REMOVE_BOOTH / C2 / FEASIBLE_CONTROL

- Scene: `test-scene-04`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 删除可用展位 D103。
- English: Remove available booth D103.
- Intent requirements: `{"required_operation_types": ["REMOVE_BOOTH"], "required_target_ids": ["scene-4-booth-03"]}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0056 — REMOVE_BOOTH / C3 / AMBIGUOUS_TARGET

- Scene: `dev-scene-01`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": true, "hide_scale": false, "hide_unit": false}`
- Chinese: 删除入口旁边的一个展位。
- English: Remove a booth beside the entrance.
- Intent requirements: `{"required_operation_types": ["REMOVE_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0057 — REMOVE_BOOTH / C3 / FEASIBLE_CONTROL

- Scene: `test-scene-05`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 E103，再把 E104 移到刚释放的位置。
- English: Remove E103, then move E104 to the newly released position.
- Intent requirements: `{"anchor_operation_type": "MOVE_BOOTH", "required_anchor": [15.0, 2.0], "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH"], "required_target_ids": ["scene-5-booth-03"], "required_targets_by_operation": {"MOVE_BOOTH": ["scene-5-booth-04"]}}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0058 — REMOVE_BOOTH / C3 / LOCKED_MUTATION

- Scene: `test-scene-06`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 F103，再把 F104 移到刚释放的位置。不得改动已售或锁定展位。
- English: Remove F103, then move F104 to the newly released position. Do not modify sold or locked booths.
- Intent requirements: `{"anchor_operation_type": "MOVE_BOOTH", "required_anchor": [15.0, 2.0], "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH"], "required_target_ids": ["scene-6-booth-03"], "required_targets_by_operation": {"MOVE_BOOTH": ["scene-6-booth-04"]}}`
- Witness present: `True`
- Probe rules: `["LOCKED_MUTATION"]`
- Review decision: **PASS**
- Review notes:

## task-0059 — REMOVE_BOOTH / C3 / AMBIGUOUS_TARGET

- Scene: `test-scene-07`; booths=12; boundary vertices=8
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": true, "hide_scale": false, "hide_unit": false}`
- Chinese: 删除入口旁边的一个展位。
- English: Remove a booth beside the entrance.
- Intent requirements: `{"required_operation_types": ["REMOVE_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0060 — REMOVE_BOOTH / C3 / FEASIBLE_CONTROL

- Scene: `test-scene-08`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 H103，再把 H104 移到刚释放的位置。
- English: Remove H103, then move H104 to the newly released position.
- Intent requirements: `{"anchor_operation_type": "MOVE_BOOTH", "required_anchor": [15.0, 2.0], "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH"], "required_target_ids": ["scene-8-booth-03"], "required_targets_by_operation": {"MOVE_BOOTH": ["scene-8-booth-04"]}}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0061 — SPLIT_BOOTH / C1 / FEASIBLE_CONTROL

- Scene: `dev-scene-02`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 B103 拆成 2 个 2×3 米展位。
- English: Split B103 into 2 booths of 2 x 3 m.
- Intent requirements: `{"count": 2, "height": 3, "required_operation_types": ["SPLIT_BOOTH"], "required_target_ids": ["scene-2-booth-03"], "width": 2}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0062 — SPLIT_BOOTH / C1 / FEASIBLE_CONTROL

- Scene: `test-scene-03`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 C103 拆成 2 个 2×3 米展位。
- English: Split C103 into 2 booths of 2 x 3 m.
- Intent requirements: `{"count": 2, "height": 3, "required_operation_types": ["SPLIT_BOOTH"], "required_target_ids": ["scene-3-booth-03"], "width": 2}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0063 — SPLIT_BOOTH / C1 / BOUNDARY

- Scene: `test-scene-04`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 D103 拆成 2 个 2×3 米展位。
- English: Split D103 into 2 booths of 2 x 3 m.
- Intent requirements: `{"count": 2, "height": 3, "required_operation_types": ["SPLIT_BOOTH"], "required_target_ids": ["scene-4-booth-03"], "width": 2}`
- Witness present: `True`
- Probe rules: `["BOUNDARY"]`
- Review decision: **PASS**
- Review notes:

## task-0064 — SPLIT_BOOTH / C1 / LOCKED_MUTATION

- Scene: `test-scene-05`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 E103 拆成 2 个 2×3 米展位。不得改动已售或锁定展位。
- English: Split E103 into 2 booths of 2 x 3 m. Do not modify sold or locked booths.
- Intent requirements: `{"count": 2, "height": 3, "required_operation_types": ["SPLIT_BOOTH"], "required_target_ids": ["scene-5-booth-03"], "width": 2}`
- Witness present: `True`
- Probe rules: `["LOCKED_MUTATION"]`
- Review decision: **PASS**
- Review notes:

## task-0065 — SPLIT_BOOTH / C1 / AMBIGUOUS_TARGET

- Scene: `test-scene-06`; booths=12; boundary vertices=6
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": true, "hide_scale": false, "hide_unit": false}`
- Chinese: 把入口旁边的一个展位拆成两个 2×3 米展位。
- English: Split a booth beside the entrance into two 2 x 3 m booths.
- Intent requirements: `{"required_operation_types": ["SPLIT_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0066 — SPLIT_BOOTH / C2 / OVERLAP

- Scene: `dev-scene-02`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 B103 拆成 2 个 2×3 米展位。
- English: Split B103 into 2 booths of 2 x 3 m.
- Intent requirements: `{"count": 2, "height": 3, "required_operation_types": ["SPLIT_BOOTH"], "required_target_ids": ["scene-2-booth-03"], "width": 2}`
- Witness present: `True`
- Probe rules: `["OVERLAP"]`
- Review decision: **PASS**
- Review notes:

## task-0067 — SPLIT_BOOTH / C2 / FEASIBLE_CONTROL

- Scene: `test-scene-07`; booths=12; boundary vertices=8
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 G103 拆成 2 个 2×3 米展位。
- English: Split G103 into 2 booths of 2 x 3 m.
- Intent requirements: `{"count": 2, "height": 3, "required_operation_types": ["SPLIT_BOOTH"], "required_target_ids": ["scene-7-booth-03"], "width": 2}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0068 — SPLIT_BOOTH / C2 / OVERLAP

- Scene: `test-scene-08`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 H103 拆成 2 个 2×3 米展位。
- English: Split H103 into 2 booths of 2 x 3 m.
- Intent requirements: `{"count": 2, "height": 3, "required_operation_types": ["SPLIT_BOOTH"], "required_target_ids": ["scene-8-booth-03"], "width": 2}`
- Witness present: `True`
- Probe rules: `["OVERLAP"]`
- Review decision: **PASS**
- Review notes:

## task-0069 — SPLIT_BOOTH / C2 / LOCKED_MUTATION

- Scene: `test-scene-03`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 把 C103 拆成 2 个 2×3 米展位。不得改动已售或锁定展位。
- English: Split C103 into 2 booths of 2 x 3 m. Do not modify sold or locked booths.
- Intent requirements: `{"count": 2, "height": 3, "required_operation_types": ["SPLIT_BOOTH"], "required_target_ids": ["scene-3-booth-03"], "width": 2}`
- Witness present: `True`
- Probe rules: `["LOCKED_MUTATION"]`
- Review decision: **PASS**
- Review notes:

## task-0070 — SPLIT_BOOTH / C2 / MISSING_EVIDENCE

- Scene: `test-scene-04`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": true, "hide_unit": true}`
- Chinese: 把 D103 拆成两个等大展位，每个宽一个网格单元，高度保持不变。
- English: Split D103 into two equal booths, each one grid cell wide with unchanged height.
- Intent requirements: `{"required_operation_types": ["SPLIT_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0071 — SPLIT_BOOTH / C3 / MISSING_EVIDENCE

- Scene: `dev-scene-02`; booths=12; boundary vertices=6
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": true, "hide_unit": true}`
- Chinese: 把 B103 拆成两个等大展位，每个宽一个网格单元，高度保持不变。
- English: Split B103 into two equal booths, each one grid cell wide with unchanged height.
- Intent requirements: `{"required_operation_types": ["SPLIT_BOOTH"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0072 — SPLIT_BOOTH / C3 / FEASIBLE_CONTROL

- Scene: `test-scene-05`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 E104，再把 E103 拆成两个 2×3 米展位并放在东侧开放区域。
- English: Remove E104, then split E103 into two 2 x 3 m booths in the open east area.
- Intent requirements: `{"count": 2, "goal_zone": "east", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "SPLIT_BOOTH"], "required_target_ids": ["scene-5-booth-03"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-5-booth-04"]}, "width": 2}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0073 — SPLIT_BOOTH / C3 / OVERLAP

- Scene: `test-scene-06`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 F104，再把 F103 拆成两个 2×3 米展位并放在东侧开放区域。
- English: Remove F104, then split F103 into two 2 x 3 m booths in the open east area.
- Intent requirements: `{"count": 2, "goal_zone": "east", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "SPLIT_BOOTH"], "required_target_ids": ["scene-6-booth-03"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-6-booth-04"]}, "width": 2}`
- Witness present: `True`
- Probe rules: `["OVERLAP"]`
- Review decision: **PASS**
- Review notes:

## task-0074 — SPLIT_BOOTH / C3 / OVERLAP

- Scene: `test-scene-07`; booths=12; boundary vertices=8
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 G104，再把 G103 拆成两个 2×3 米展位并放在东侧开放区域。
- English: Remove G104, then split G103 into two 2 x 3 m booths in the open east area.
- Intent requirements: `{"count": 2, "goal_zone": "east", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "SPLIT_BOOTH"], "required_target_ids": ["scene-7-booth-03"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-7-booth-04"]}, "width": 2}`
- Witness present: `True`
- Probe rules: `["OVERLAP"]`
- Review decision: **PASS**
- Review notes:

## task-0075 — SPLIT_BOOTH / C3 / PROTECTED_POLYGON

- Scene: `test-scene-08`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 H104，再把 H103 拆成两个 2×3 米展位并放在东侧开放区域。
- English: Remove H104, then split H103 into two 2 x 3 m booths in the open east area.
- Intent requirements: `{"count": 2, "goal_zone": "east", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "SPLIT_BOOTH"], "required_target_ids": ["scene-8-booth-03"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-8-booth-04"]}, "width": 2}`
- Witness present: `True`
- Probe rules: `["PROTECTED_POLYGON"]`
- Review decision: **PASS**
- Review notes:

## task-0076 — RESERVE_AISLE / C1 / FEASIBLE_CONTROL

- Scene: `dev-scene-01`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在南侧开放区域预留一条 2×5 米通道。
- English: Reserve a 2 x 5 m aisle in the open south area.
- Intent requirements: `{"goal_zone": "south", "height": 5, "required_operation_types": ["RESERVE_AISLE"], "width": 2}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0077 — RESERVE_AISLE / C1 / FEASIBLE_CONTROL

- Scene: `test-scene-03`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在南侧开放区域预留一条 2×5 米通道。
- English: Reserve a 2 x 5 m aisle in the open south area.
- Intent requirements: `{"goal_zone": "south", "height": 5, "required_operation_types": ["RESERVE_AISLE"], "width": 2}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0078 — RESERVE_AISLE / C1 / BOUNDARY

- Scene: `test-scene-04`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在南侧开放区域预留一条 2×5 米通道。
- English: Reserve a 2 x 5 m aisle in the open south area.
- Intent requirements: `{"goal_zone": "south", "height": 5, "required_operation_types": ["RESERVE_AISLE"], "width": 2}`
- Witness present: `True`
- Probe rules: `["BOUNDARY"]`
- Review decision: **PASS**
- Review notes:

## task-0079 — RESERVE_AISLE / C1 / PROTECTED_POLYGON

- Scene: `test-scene-05`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在南侧开放区域预留一条 2×5 米通道。
- English: Reserve a 2 x 5 m aisle in the open south area.
- Intent requirements: `{"goal_zone": "south", "height": 5, "required_operation_types": ["RESERVE_AISLE"], "width": 2}`
- Witness present: `True`
- Probe rules: `["PROTECTED_POLYGON"]`
- Review decision: **PASS**
- Review notes:

## task-0080 — RESERVE_AISLE / C1 / AMBIGUOUS_TARGET

- Scene: `test-scene-06`; booths=12; boundary vertices=6
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": true, "hide_scale": false, "hide_unit": false}`
- Chinese: 在入口旁边预留一条 2×5 米通道。
- English: Reserve a 2 x 5 m aisle beside the entrance.
- Intent requirements: `{"required_operation_types": ["RESERVE_AISLE"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0081 — RESERVE_AISLE / C2 / PROTECTED_POLYGON

- Scene: `dev-scene-01`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在南侧开放区域预留一条 2×5 米通道。
- English: Reserve a 2 x 5 m aisle in the open south area.
- Intent requirements: `{"goal_zone": "south", "height": 5, "required_operation_types": ["RESERVE_AISLE"], "width": 2}`
- Witness present: `True`
- Probe rules: `["PROTECTED_POLYGON"]`
- Review decision: **PASS**
- Review notes:

## task-0082 — RESERVE_AISLE / C2 / FEASIBLE_CONTROL

- Scene: `test-scene-07`; booths=12; boundary vertices=8
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在南侧开放区域预留一条 2×5 米通道。
- English: Reserve a 2 x 5 m aisle in the open south area.
- Intent requirements: `{"goal_zone": "south", "height": 5, "required_operation_types": ["RESERVE_AISLE"], "width": 2}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0083 — RESERVE_AISLE / C2 / BOUNDARY

- Scene: `test-scene-08`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在南侧开放区域预留一条 2×5 米通道。
- English: Reserve a 2 x 5 m aisle in the open south area.
- Intent requirements: `{"goal_zone": "south", "height": 5, "required_operation_types": ["RESERVE_AISLE"], "width": 2}`
- Witness present: `True`
- Probe rules: `["BOUNDARY"]`
- Review decision: **PASS**
- Review notes:

## task-0084 — RESERVE_AISLE / C2 / PROTECTED_POLYGON

- Scene: `test-scene-03`; booths=12; boundary vertices=4
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 在南侧开放区域预留一条 2×5 米通道。
- English: Reserve a 2 x 5 m aisle in the open south area.
- Intent requirements: `{"goal_zone": "south", "height": 5, "required_operation_types": ["RESERVE_AISLE"], "width": 2}`
- Witness present: `True`
- Probe rules: `["PROTECTED_POLYGON"]`
- Review decision: **PASS**
- Review notes:

## task-0085 — RESERVE_AISLE / C2 / AMBIGUOUS_TARGET

- Scene: `test-scene-04`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": true, "hide_scale": false, "hide_unit": false}`
- Chinese: 在入口旁边预留一条 2×5 米通道。
- English: Reserve a 2 x 5 m aisle beside the entrance.
- Intent requirements: `{"required_operation_types": ["RESERVE_AISLE"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0086 — RESERVE_AISLE / C3 / AMBIGUOUS_TARGET

- Scene: `dev-scene-01`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": true, "hide_scale": false, "hide_unit": false}`
- Chinese: 在入口旁边预留一条 2×5 米通道。
- English: Reserve a 2 x 5 m aisle beside the entrance.
- Intent requirements: `{"required_operation_types": ["RESERVE_AISLE"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0087 — RESERVE_AISLE / C3 / FEASIBLE_CONTROL

- Scene: `test-scene-05`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 E104，再在南侧开放区域预留一条 4×3 米通道。
- English: Remove E104, then reserve a 4 x 3 m aisle in the open south area.
- Intent requirements: `{"goal_zone": "south", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "RESERVE_AISLE"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-5-booth-04"]}, "width": 4}`
- Witness present: `True`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:

## task-0088 — RESERVE_AISLE / C3 / PROTECTED_POLYGON

- Scene: `test-scene-06`; booths=12; boundary vertices=6
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 F104，再在南侧开放区域预留一条 4×3 米通道。
- English: Remove F104, then reserve a 4 x 3 m aisle in the open south area.
- Intent requirements: `{"goal_zone": "south", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "RESERVE_AISLE"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-6-booth-04"]}, "width": 4}`
- Witness present: `True`
- Probe rules: `["PROTECTED_POLYGON"]`
- Review decision: **PASS**
- Review notes:

## task-0089 — RESERVE_AISLE / C3 / PROTECTED_POLYGON

- Scene: `test-scene-07`; booths=12; boundary vertices=8
- Admissible outcome: `VALID_EDIT`
- Context mask: `{"hide_disambiguating_labels": false, "hide_scale": false, "hide_unit": false}`
- Chinese: 先删除 G104，再在南侧开放区域预留一条 4×3 米通道。
- English: Remove G104, then reserve a 4 x 3 m aisle in the open south area.
- Intent requirements: `{"goal_zone": "south", "height": 3, "required_operation_types": ["REMOVE_BOOTH", "RESERVE_AISLE"], "required_targets_by_operation": {"REMOVE_BOOTH": ["scene-7-booth-04"]}, "width": 4}`
- Witness present: `True`
- Probe rules: `["PROTECTED_POLYGON"]`
- Review decision: **PASS**
- Review notes:

## task-0090 — RESERVE_AISLE / C3 / AMBIGUOUS_TARGET

- Scene: `test-scene-08`; booths=12; boundary vertices=4
- Admissible outcome: `DEFER`
- Context mask: `{"hide_disambiguating_labels": true, "hide_scale": false, "hide_unit": false}`
- Chinese: 在入口旁边预留一条 2×5 米通道。
- English: Reserve a 2 x 5 m aisle beside the entrance.
- Intent requirements: `{"required_operation_types": ["RESERVE_AISLE"]}`
- Witness present: `False`
- Probe rules: `[]`
- Review decision: **PASS**
- Review notes:
