# Run it yourself

```bash
uv sync --extra dev
cp .env.example .env      # add SECUREAGENT_OPENAI_API_KEY when a live model is wanted
make dev                  # http://localhost:8000/healthz
make check                # ruff, mypy --strict, import-linter, pytest
make eval                 # canonical eval and attack suite
```

`zarreh-agentkit` is resolved over https from a public git tag, so no
credentials are needed.
