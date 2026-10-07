# Providers, Models & Reasoning Controls

PDLt interacts with upstream frontier LLMs via unified provider adapters, supporting multi-provider fallback, structured schema compliance, and fine-grained operation-level reasoning effort control.

---

## Provider Architecture

PDLt accesses models through OpenRouter or direct provider endpoints:
- **System 1 (Routing & Guardrails)**: Lightweight routing model evaluating policy scopes, network permissions, and knowledge cutoffs.
- **System 2 (Interpretation, Planning & Execution)**: Frontier reasoning models (e.g. `openai/gpt-oss-120b`, `nvidia/nemotron-3-super-120b-a12b`, Anthropic Claude, OpenAI o-series).

---

## Reasoning Effort Controls

PDLt allows setting global reasoning effort as well as per-operation overrides:

```bash
# Global reasoning effort
python run_catalogue.py --model openai/gpt-oss-120b --reasoning low

# Per-operation reasoning override
python run_catalogue.py \
  --model openai/gpt-oss-120b \
  --reasoning low \
  --reasoning-op EXECUTE=medium
```

### Supported Operations for Reasoning Control

- `BOOTSTRAP_ANALYSIS`: Initial prompt classification and semantic extraction.
- `DRAFT_PROMPT`: High-level user intent interpretation in pseudocode.
- `DRAFT_PLAN`: Algorithmic and structural planning in pseudocode.
- `EXECUTE`: Deliverable code authoring.
- `VERIFY_REPAIR`: Diagnostic analysis and error correction in the sandbox loop.

---

## Resilience & Retry Policies

- **Deterministic Evaluation**: In catalogue evaluation mode, retries and do-overs are strictly prohibited (1 attempt per prompt).
- **HTTP / Provider Faults**: Network timeouts or transient 5xx errors from providers are captured and classified as `HARNESS_ERROR` rather than model failure outcomes.
