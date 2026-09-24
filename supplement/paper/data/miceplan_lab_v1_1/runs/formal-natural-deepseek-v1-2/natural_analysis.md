# Formal Held-Out Natural-Incidence Audit — formal-natural-deepseek-v1-2

## Completion and isolation

- Policy outcomes: 1080/1080
- Unique model calls: 442
- Infrastructure error records: 2
- Held-out request IDs observed: ['task-0002-en', 'task-0002-zh', 'task-0003-en', 'task-0003-zh', 'task-0004-en', 'task-0004-zh', 'task-0005-en', 'task-0005-zh', 'task-0007-en', 'task-0007-zh', 'task-0008-en', 'task-0008-zh', 'task-0009-en', 'task-0009-zh', 'task-0010-en', 'task-0010-zh', 'task-0012-en', 'task-0012-zh', 'task-0013-en', 'task-0013-zh', 'task-0014-en', 'task-0014-zh', 'task-0015-en', 'task-0015-zh', 'task-0017-en', 'task-0017-zh', 'task-0018-en', 'task-0018-zh', 'task-0019-en', 'task-0019-zh', 'task-0020-en', 'task-0020-zh', 'task-0022-en', 'task-0022-zh', 'task-0023-en', 'task-0023-zh', 'task-0024-en', 'task-0024-zh', 'task-0025-en', 'task-0025-zh', 'task-0027-en', 'task-0027-zh', 'task-0028-en', 'task-0028-zh', 'task-0029-en', 'task-0029-zh', 'task-0030-en', 'task-0030-zh', 'task-0032-en', 'task-0032-zh', 'task-0033-en', 'task-0033-zh', 'task-0034-en', 'task-0034-zh', 'task-0035-en', 'task-0035-zh', 'task-0037-en', 'task-0037-zh', 'task-0038-en', 'task-0038-zh', 'task-0039-en', 'task-0039-zh', 'task-0040-en', 'task-0040-zh', 'task-0042-en', 'task-0042-zh', 'task-0043-en', 'task-0043-zh', 'task-0044-en', 'task-0044-zh', 'task-0045-en', 'task-0045-zh', 'task-0047-en', 'task-0047-zh', 'task-0048-en', 'task-0048-zh', 'task-0049-en', 'task-0049-zh', 'task-0050-en', 'task-0050-zh', 'task-0052-en', 'task-0052-zh', 'task-0053-en', 'task-0053-zh', 'task-0054-en', 'task-0054-zh', 'task-0055-en', 'task-0055-zh', 'task-0057-en', 'task-0057-zh', 'task-0058-en', 'task-0058-zh', 'task-0059-en', 'task-0059-zh', 'task-0060-en', 'task-0060-zh', 'task-0062-en', 'task-0062-zh', 'task-0063-en', 'task-0063-zh', 'task-0064-en', 'task-0064-zh', 'task-0065-en', 'task-0065-zh', 'task-0067-en', 'task-0067-zh', 'task-0068-en', 'task-0068-zh', 'task-0069-en', 'task-0069-zh', 'task-0070-en', 'task-0070-zh', 'task-0072-en', 'task-0072-zh', 'task-0073-en', 'task-0073-zh', 'task-0074-en', 'task-0074-zh', 'task-0075-en', 'task-0075-zh', 'task-0077-en', 'task-0077-zh', 'task-0078-en', 'task-0078-zh', 'task-0079-en', 'task-0079-zh', 'task-0080-en', 'task-0080-zh', 'task-0082-en', 'task-0082-zh', 'task-0083-en', 'task-0083-zh', 'task-0084-en', 'task-0084-zh', 'task-0085-en', 'task-0085-zh', 'task-0087-en', 'task-0087-zh', 'task-0088-en', 'task-0088-zh', 'task-0089-en', 'task-0089-zh', 'task-0090-en', 'task-0090-zh']
- Estimated unique API cost: USD 0.3420

## Formal policy metrics

| Policy | n | RIOER | UER | STS | SRR | Block | Defer | Mean calls | Cost (USD) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LLM_ONLY | 216 | 4.2% | 74.1% | 23.6% | 24.5% | 1.4% | 0.9% | 1.00 | 0.1519 |
| CONSTRAINT_IN_PROMPT | 216 | 10.6% | 63.9% | 32.9% | 34.7% | 1.4% | 1.9% | 1.00 | 0.1738 |
| VALIDATE_AND_BLOCK | 216 | 0.0% | 5.6% | 23.6% | 24.5% | 1.4% | 69.4% | 1.00 | 0.1519 |
| VALIDATE_AND_REPAIR | 216 | 0.0% | 5.6% | 25.0% | 25.9% | 0.0% | 69.4% | 1.03 | 0.1622 |
| VALIDATE_AND_BLIND_RETRY | 216 | 0.0% | 5.6% | 24.5% | 25.5% | 0.0% | 69.9% | 1.02 | 0.1579 |

## Natural-failure repair diagnostics

### VALIDATE_AND_REPAIR

Initial independently failed cases: 9

| Attempt | Entered | Newly recovered | Marginal recovery | Recovery@k |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 3 | 1 | 33.3% | 11.1% |
| 2 | 2 | 1 | 50.0% | 22.2% |
| 3 | 1 | 1 | 100.0% | 33.3% |

Repeated-violation rate: 16.7%; rule-regression rate: 33.3%.

### VALIDATE_AND_BLIND_RETRY

Initial independently failed cases: 9

| Attempt | Entered | Newly recovered | Marginal recovery | Recovery@k |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 3 | 2 | 66.7% | 22.2% |
| 2 | 1 | 0 | 0.0% | 22.2% |
| 3 | 0 | 0 | n/a | 22.2% |

Repeated-violation rate: 25.0%; rule-regression rate: 0.0%.

These are formal held-out natural-incidence results. Conditional seeded-recovery results remain a separate Track S estimand and must not be pooled into this table.
