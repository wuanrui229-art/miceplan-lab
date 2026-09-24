# MICEPlan-Lab Second-Model Freeze — 2026-07-21

**Formal responses observed:** none.  
**Internal bilingual surface-form QA:** passed on 2026-07-22; this is not
practitioner or CAD-domain expert validation.  
**Status:** second-family configuration frozen for later formal robustness analysis.

## Frozen secondary configuration

- Family/provider: DeepSeek Open Platform;
- model identifier: `deepseek-v4-pro`;
- endpoint: `https://api.deepseek.com/beta/chat/completions`;
- thinking: explicitly disabled;
- temperature: provider default;
- maximum output tokens: 32,768;
- output: forced strict function tool on the beta endpoint;
- nullable operation fields: reversible `__MICEPLAN_NULL__` wire sentinel, decoded
  before validation against the unchanged LayoutEditIR schema;
- semantic repair limit in the formal runner: the same bounded limit and schedule as
  the primary Kimi configuration;
- pricing record: `PRICING_DEEPSEEK_V4_PRO_2026-07-21.json`.

The successful development qualification produced 8/8 schema-valid outputs, no
truncation, and no infrastructure errors. Its run ID and all provider-contract failures
are listed in `DEEPSEEK_QUALIFICATION_RESULT_2026-07-21.md`.

## Formal role

Moonshot Kimi K2.7 Code HighSpeed remains the primary model. DeepSeek V4 Pro is the
genuinely different secondary model family for the pre-specified model robustness
stratum. It must use the same selected Track N and Track S jobs, visible evidence,
policy definitions, retry bounds, and independent oracle as the primary model. Results
must be reported by model before any pooled summary.

No formal call is permitted until the internal surface-form QA and all remaining v1.2
freeze checks are complete. This file freezes the model configuration only; it does
not waive those gates.
