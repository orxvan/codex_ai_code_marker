在生成或大幅改写代码时，请对 AI 生成代码加精确标记：

```text
# AI-GENERATED-BEGIN agent=Tongyi-Lingma model=<model> prompt=<short-tag>
... generated code ...
# AI-GENERATED-END
```

执行规则：

- 使用目标语言原生注释格式。
- BEGIN 和 END 必须成对出现。
- 仅标记本次 AI 实际生成的连续代码。
- 不要把纯人工修改的代码包进去。
- 如果继续在已标记块内补写代码，沿用原块边界。
