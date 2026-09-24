# Seeded Recovery Audit — formal-seeded-deepseek-v1-2

## Completion and isolation

- Policy outcomes: 630/630
- Unique repair calls: 580
- Infrastructure error records: 0
- Held-out request IDs observed: ['task-0003-en', 'task-0003-zh', 'task-0004-en', 'task-0004-zh', 'task-0007-en', 'task-0007-zh', 'task-0008-en', 'task-0008-zh', 'task-0009-en', 'task-0009-zh', 'task-0012-en', 'task-0012-zh', 'task-0013-en', 'task-0013-zh', 'task-0014-en', 'task-0014-zh', 'task-0018-en', 'task-0018-zh', 'task-0019-en', 'task-0019-zh', 'task-0022-en', 'task-0022-zh', 'task-0023-en', 'task-0023-zh', 'task-0024-en', 'task-0024-zh', 'task-0027-en', 'task-0027-zh', 'task-0028-en', 'task-0028-zh', 'task-0029-en', 'task-0029-zh', 'task-0030-en', 'task-0030-zh', 'task-0062-en', 'task-0062-zh', 'task-0063-en', 'task-0063-zh', 'task-0064-en', 'task-0064-zh', 'task-0067-en', 'task-0067-zh', 'task-0068-en', 'task-0068-zh', 'task-0069-en', 'task-0069-zh', 'task-0072-en', 'task-0072-zh', 'task-0073-en', 'task-0073-zh', 'task-0074-en', 'task-0074-zh', 'task-0075-en', 'task-0075-zh', 'task-0077-en', 'task-0077-zh', 'task-0078-en', 'task-0078-zh', 'task-0079-en', 'task-0079-zh', 'task-0082-en', 'task-0082-zh', 'task-0083-en', 'task-0083-zh', 'task-0084-en', 'task-0084-zh', 'task-0087-en', 'task-0087-zh', 'task-0088-en', 'task-0088-zh', 'task-0089-en', 'task-0089-zh']
- Held-out seed IDs observed: ['seed-task-0003-boundary+overlap', 'seed-task-0003-protected_polygon', 'seed-task-0004-boundary+protected_polygon', 'seed-task-0004-protected_polygon', 'seed-task-0007-boundary+overlap', 'seed-task-0007-overlap', 'seed-task-0008-overlap+protected_polygon', 'seed-task-0008-protected_polygon', 'seed-task-0009-overlap+protected_polygon', 'seed-task-0009-protected_polygon', 'seed-task-0012-boundary+overlap', 'seed-task-0012-overlap', 'seed-task-0013-boundary+protected_polygon', 'seed-task-0013-overlap', 'seed-task-0014-boundary+protected_polygon', 'seed-task-0014-protected_polygon', 'seed-task-0018-overlap+protected_polygon', 'seed-task-0018-protected_polygon', 'seed-task-0019-overlap+protected_polygon', 'seed-task-0019-protected_polygon', 'seed-task-0022-boundary', 'seed-task-0022-boundary+protected_polygon', 'seed-task-0023-boundary+overlap', 'seed-task-0023-overlap', 'seed-task-0024-boundary+overlap', 'seed-task-0024-overlap', 'seed-task-0027-boundary+protected_polygon', 'seed-task-0027-protected_polygon', 'seed-task-0028-boundary+protected_polygon', 'seed-task-0028-overlap', 'seed-task-0029-boundary+overlap', 'seed-task-0029-overlap', 'seed-task-0030-boundary+overlap', 'seed-task-0030-overlap', 'seed-task-0062-boundary', 'seed-task-0062-overlap+protected_polygon', 'seed-task-0063-boundary+protected_polygon', 'seed-task-0063-overlap', 'seed-task-0064-boundary', 'seed-task-0064-overlap+protected_polygon', 'seed-task-0067-overlap', 'seed-task-0067-overlap+protected_polygon', 'seed-task-0068-boundary+overlap', 'seed-task-0068-overlap', 'seed-task-0069-overlap+protected_polygon', 'seed-task-0069-protected_polygon', 'seed-task-0072-boundary+protected_polygon', 'seed-task-0072-protected_polygon', 'seed-task-0073-boundary+protected_polygon', 'seed-task-0073-protected_polygon', 'seed-task-0074-boundary', 'seed-task-0074-boundary+overlap', 'seed-task-0075-overlap', 'seed-task-0075-overlap+protected_polygon', 'seed-task-0077-boundary', 'seed-task-0078-boundary', 'seed-task-0079-boundary', 'seed-task-0082-boundary', 'seed-task-0083-boundary', 'seed-task-0084-boundary', 'seed-task-0087-boundary', 'seed-task-0088-boundary', 'seed-task-0089-boundary']
- Estimated unique API cost: USD 0.4583

## Seed and feedback audits

- Every initial candidate failed independently: True
- Every seed preserved the task intent signature: True
- Every initial rule set matched its declared seed rule: True
- Rule/blind prompt isolation passed: True

## Policy results

| Policy | n | Safe task success | Median total latency | Mean calls | Cost (USD) |
| --- | ---: | ---: | ---: | ---: | ---: |
| SEEDED_VALIDATE_AND_BLOCK | 210 | 0.0% | 0.00 s | 0.00 | 0.0000 |
| SEEDED_VALIDATE_AND_REPAIR | 210 | 66.2% | 4.01 s | 1.38 | 0.2397 |
| SEEDED_VALIDATE_AND_BLIND_RETRY | 210 | 64.8% | 3.47 s | 1.38 | 0.2187 |

## Paired rule-feedback versus blind retry

- Paired cases: 210
- Both succeeded: 106
- Rule feedback only succeeded: 33
- Blind retry only succeeded: 30
- Neither succeeded: 41
- Median attempt difference (rule minus blind): 0.0

## Interpretation boundary

This formal held-out seeded-recovery experiment estimates conditional recovery from transparent, intent-preserving injected failures. It does not estimate how often the LLM naturally creates those failures and should be analyzed separately from Track N.
