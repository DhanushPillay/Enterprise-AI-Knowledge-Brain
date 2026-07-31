# Model Card: Llama 3.1 8B Instant (Groq)

## Model Information

| Field | Value |
|-------|-------|
| Provider | Groq (hosted) |
| Model ID | `llama-3.1-8b-instant` |
| Architecture | Transformer (Llama 3.1) |
| Parameters | 8 billion |
| Context Window | 128K tokens |
| Max Output | 8,192 tokens |
| License | Llama 3.1 Community License |

## Intended Use

- Bulk entity extraction (high volume, simple format)
- Text classification
- Simple prompt-response tasks
- Prompt injection detection (classifier)

## Rate Limits (Free Tier)

| Limit | Value |
|-------|-------|
| RPM | 30 |
| TPM | 6,000 |
| RPD | 14,400 |

## Performance Characteristics

- **Strengths:** Fast inference, high daily limit, good for structured tasks
- **Weaknesses:** Less capable for complex reasoning
- **Best for:** High-volume, simple tasks

## Usage in This Project

```python
entities = await client.generate_structured(
    prompt=f"Extract entities from:\n{text}",
    schema=entity_schema,
    model="llama-3.1-8b-instant",
    temperature=0.0,
)
```

## Limitations

- Not suitable for complex reasoning tasks (use 70B model)
- May struggle with ambiguous or nuanced text
- No fine-tuning available on Groq
- Knowledge cutoff: early 2025

## Ethical Considerations

- Lower quality than 70B model — verify critical outputs
- Entity extraction may miss or misclassify entities
- Should be combined with human review for important data
