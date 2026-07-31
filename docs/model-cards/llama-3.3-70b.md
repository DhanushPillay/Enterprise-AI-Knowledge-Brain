# Model Card: Llama 3.3 70B Versatile (Groq)

## Model Information

| Field | Value |
|-------|-------|
| Provider | Groq (hosted) |
| Model ID | `llama-3.3-70b-versatile` |
| Architecture | Transformer (Llama 3.3) |
| Parameters | 70 billion |
| Context Window | 128K tokens |
| Max Output | 32,768 tokens |
| License | Llama 3.3 Community License |

## Intended Use

- Query answering (requires reasoning)
- Complex entity extraction (ambiguous text)
- Answer generation with citations
- Text summarization
- Multi-step reasoning tasks

## Rate Limits (Free Tier)

| Limit | Value |
|-------|-------|
| RPM | 30 |
| TPM | 6,000 |
| RPD | 1,000 |

## Performance Characteristics

- **Strengths:** Complex reasoning, instruction following, multi-step tasks
- **Weaknesses:** Slower than 8B model, lower daily limit
- **Best for:** Tasks requiring accuracy over speed

## Usage in This Project

```python
answer = await client.generate(
    prompt=f"Answer using ONLY this context:\n{context}\n\nQuestion: {question}",
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    max_tokens=2048,
)
```

## Limitations

- Not suitable for high-volume extraction (use 8B model)
- Rate limits require batching and retry logic
- No fine-tuning available on Groq
- Knowledge cutoff: early 2025

## Ethical Considerations

- May generate plausible but incorrect answers
- Should not be used for medical, legal, or financial advice without human review
- Citations should be verified against source documents
