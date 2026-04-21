When you generate or heavily rewrite code, wrap the AI-authored region with exact markers:

```text
# AI-GENERATED-BEGIN agent=Claude model=<model> prompt=<short-tag>
... generated code ...
# AI-GENERATED-END
```

Rules:

- Use the existing comment syntax of the target language.
- Do not omit the END marker.
- Only wrap the smallest contiguous AI-authored block.
- Do not wrap user-authored edits unless they were generated in the same response.
- Preserve markers unless the whole AI-authored block is intentionally rewritten by a human.
