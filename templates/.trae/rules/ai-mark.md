在生成或大幅改写代码时，必须使用 AI 标记包裹生成区块，格式如下：

```text
# AI-GENERATED-BEGIN agent=Trae model=<model> prompt=<short-tag>
... generated code ...
# AI-GENERATED-END
```

要求：

- 使用目标语言已有的注释语法。
- 只包裹连续的 AI 生成代码块。
- 不要遗漏 END 标记。
- 如果用户只让你修改 1-2 行，不要扩大包裹范围。
- 除非整段被人类重写，否则保留原有标记。
