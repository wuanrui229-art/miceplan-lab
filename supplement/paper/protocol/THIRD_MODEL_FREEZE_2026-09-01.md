# Third-model freeze: OpenAI GPT-5.6 Sol

Date frozen: 2026-09-01  
Evidence status: reviewer-requested model-coverage extension; no GPT-5.6 Sol held-out response observed

## Selection rule

The third provider was selected before any GPT-5.6 Sol development or held-out call. Selection
was based on provider-family diversity, flagship positioning, availability through a documented
API, strict JSON Schema support, and the ability to disable explicit reasoning. The model was not
selected after observing benchmark outcomes.

## Frozen provider configuration

- provider: OpenAI API
- model ID: `gpt-5.6-sol`
- endpoint: `https://api.openai.com/v1/chat/completions`
- output contract: provider-enforced `response_format` strict JSON Schema
- explicit reasoning: `reasoning_effort: none`
- temperature: omitted
- maximum completion tokens: 32,768 via `max_completion_tokens`
- response storage: disabled with `store: false`
- infrastructure retry bound: 3 attempts for transient transport or HTTP failures only
- semantic repair limit: 3
- credential source: environment variable or macOS Keychain; plaintext is never serialized

The 32,768-token cap matches the two previously frozen provider configurations while remaining
below the model's documented maximum. Provider-native decoding controls are recorded rather than
treated as identical across APIs.

## Formal scope after development qualification

- Track N: the complete 216-job held-out natural-incidence schedule
- Track S: the complete 210-job held-out seeded conditional-recovery schedule
- same frozen prompts, schema, task selections, policy arms, replicate schedule, and offline
  evaluation code as the prior two formal models

Formal held-out execution remains prohibited until a development-only compatibility run is
reviewed and separately authorized by the author.

## Official sources checked on 2026-09-01

- model and pricing: https://developers.openai.com/api/docs/models/gpt-5.6-sol
- Chat Completions parameters: https://developers.openai.com/api/reference/cli/resources/chat/subresources/completions/methods/create
