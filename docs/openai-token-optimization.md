# OpenAI Token Optimization for RAG Pipelines (2025)

This document outlines optimal token settings for OpenAI models in RAG applications, based on research conducted in January 2025.

## Executive Summary

**Best Practice**: For OpenAI models, `max_tokens` can be safely set OR omitted. Unlike Gemini, there are no known bugs with either approach.

## User Preference

**Preferred Implementation**: Do not set max_tokens or any token limits at all. Let all models use their defaults for maximum flexibility. This approach:
- Allows models to use available context intelligently
- Simplifies the codebase by removing configuration complexity
- Works reliably with all OpenAI models (GPT-4, o3, etc.)
- Ensures consistent behavior across different providers

## Model-Specific Parameter Differences

### 🎯 GPT-4.1 (Generative Models)
- **Parameter**: `max_tokens`
- **Maximum**: 32,768 output tokens
- **Default when omitted**: "inf" (capped by model limit)
- **Temperature**: Fully supported
- **Recommendation**: Safe to set 1000-2000 for RAG responses

### 🧠 o3 Series (Reasoning Models)
- **Parameter**: `max_completion_tokens` (NOT `max_tokens`)
- **Maximum**: 100,000 output tokens
- **Temperature**: NOT supported (but API handles gracefully when omitted)
- **Hidden tokens**: Uses internal reasoning tokens not visible in output
- **Updated Recommendation**: Per user preference, don't set any parameters - o3 works fine with defaults

## Default Behavior Analysis

### When `max_tokens` is Omitted

1. **Theory**: Defaults to infinity ("inf")
2. **Practice**: Limited by:
   - Model's maximum output capacity
   - Remaining context window after input tokens
3. **No bugs**: Unlike Gemini, works reliably

### Model Output Limits

| Model | Max Output Tokens | Context Window | Parameter Name |
|-------|------------------|----------------|----------------|
| GPT-4.1 | 32,768 | 1M | `max_tokens` |
| GPT-4o | 16,384 | 128K | `max_tokens` |
| GPT-4 | 4,096 | 128K | `max_tokens` |
| o3 | 100,000 | 200K | `max_completion_tokens` |
| o3-mini | 100,000 | 128K | `max_completion_tokens` |

## Implementation Guidelines

### ✅ Recommended Configuration (User Preference)

```python
def call_llm_openai(prompt: str, model: str = None) -> str:
    """Call OpenAI's API - works with all models including o3."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # All models: let them use their defaults
    # Note: o3 models don't support temperature, but OpenAI handles this gracefully
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
        # No parameters set - let models use their optimal defaults
    )
    return response.choices[0].message.content
```

**Benefits of this approach:**
- Works with ALL OpenAI models (GPT-4, o3, future models)
- o3 can use its full 100k token capacity when needed
- No need for model-specific logic
- Simplest possible implementation

### 🚀 RAG-Specific Recommendations

For RAG pipelines with OpenAI:

1. **Option 1: Set explicit limit**
   ```python
   kwargs = {"max_tokens": 1000}  # Good for concise answers
   ```

2. **Option 2: Let model decide**
   ```python
   kwargs = {}  # Model uses available context
   ```

Both options work well - choose based on your needs:
- **Set limit**: For predictable response lengths and cost control
- **No limit**: For complex answers that may need more tokens

## Comparison with Gemini

### Key Differences

| Aspect | OpenAI | Gemini |
|--------|---------|---------|
| Omit max_tokens | ✅ Works fine | ❌ Can cause empty responses |
| Set max_tokens | ✅ Works as expected | ⚠️ May cause issues with 2.5 Pro |
| Best practice | Either approach | Avoid setting max_tokens |

## Cost Considerations

### Token Usage Impact

- **With limit**: Predictable costs, may truncate complex answers
- **Without limit**: Higher potential costs, complete answers
- **Recommendation**: Set reasonable limits (1000-2000) for production RAG

### Reasoning Models (o3)

- **Hidden cost**: Internal reasoning tokens (not visible)
- **Example**: 200-token answer might use 10,000 reasoning tokens
- **Budget accordingly**: o3 models are more expensive per query

## Troubleshooting

### Updated Findings

1. **o3 Parameter Handling**:
   ```python
   # ✅ Recommended - works for ALL models including o3
   {"model": "o3"}  # No parameters needed
   
   # Also valid if you need to limit tokens:
   {"model": "o3", "max_completion_tokens": 1000}
   ```

2. **Temperature with o3**:
   ```python
   # ✅ Best practice - don't set temperature for any model
   {"model": "o3"}  # OpenAI handles o3's lack of temperature support
   ```

**Key Discovery**: o3 models work perfectly fine without setting `max_completion_tokens`. When omitted, they can use their full 100k token capacity as needed.

## Best Practices Summary

### For RAG Applications

1. **GPT-4.1 (default)**: Safe to set `max_tokens` to 1000-2000
2. **Cost control**: Always set limits in production
3. **Quality**: Test with/without limits for your use case
4. **o3 models**: Use only for complex reasoning, not general RAG

### Parameter Checklist

- [ ] Use correct parameter name (`max_tokens` vs `max_completion_tokens`)
- [ ] Remove temperature for o3 models
- [ ] Set reasonable limits for cost control
- [ ] Test thoroughly with your specific prompts

---

*Document created: January 2025*  
*Last updated: January 10, 2025*  
*Research basis: OpenAI Developer Forums, Official API Documentation*