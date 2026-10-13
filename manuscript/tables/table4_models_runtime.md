# Table 4 — Models and runtime settings

| Model | Condition | Backend | Max new tokens | Sampling | Thinking mode | Seed | Embedding model | Passages per layer |
|---|---|---|---:|---|---|---:|---|---:|
| Qwen/Qwen3-8B | B0 | transformers | 512 | greedy | off | 42 | – | – |
| Qwen/Qwen3-8B | B1 | transformers | 512 | greedy | off | 42 | – | – |
| Qwen/Qwen3-8B | B5 | transformers | 512 | greedy | off | 42 | qwen3-embedding-4b | 3 |
| Qwen/Qwen3-14B-AWQ | B0 | transformers | 512 | greedy | off | 42 | – | – |
| Qwen/Qwen3-14B-AWQ | B5 | transformers | 512 | greedy | off | 42 | qwen3-embedding-4b | 3 |
| Qwen/Qwen3-32B-AWQ | B0 | transformers | 512 | greedy | off | 42 | – | – |
| Qwen/Qwen3-32B-AWQ | B5 | transformers | 512 | greedy | off | 42 | qwen3-embedding-4b | 3 |

*Source: each run's config.yaml and responses.jsonl generation_config.*
