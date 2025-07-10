# Temperature Parameter Guide for LLM APIs (2025)

This document outlines best practices for handling temperature parameters across different LLM providers, based on research and implementation experience in January 2025.

## Executive Summary

**Universal Best Practice**: Remove global temperature settings from configuration files. Use model-specific defaults and only pass temperature when explicitly needed.

## User Preference

**Preferred Implementation**: Do not set temperature parameters at all. Let all models use their native defaults for optimal performance and maximum compatibility. This simplifies the codebase and ensures models can intelligently manage their own parameters based on the task at hand.

## Background

Temperature controls the randomness of model outputs:
- **0.0**: Deterministic, most likely tokens
- **1.0**: Balanced creativity and coherence (typical default)
- **2.0**: Very creative, potentially incoherent

## Provider-Specific Findings

### 🚨 OpenAI o3 Series (Reasoning Models)

**Important Note**: o3 models do NOT support the temperature parameter.

```python
# ✅ Recommended usage for o3 (and all models per user preference)
response = client.chat.completions.create(
    model="o3",
    messages=messages
    # No parameters - let model use defaults
)
```

**Key Finding**: While o3 doesn't support temperature, OpenAI's API handles this gracefully when no temperature is specified. This aligns perfectly with the user preference to not set any parameters.

### ✅ OpenAI GPT Series (Generative Models)

GPT-4.1 and other generative models fully support temperature:
- **Default**: 1.0 (when not specified)
- **Range**: 0.0 to 2.0
- **Recommendation**: Use model default unless specific need

### 🌐 Google Gemini Models

Gemini models support temperature but work best with defaults:
- **Supported**: Yes, temperature parameter works
- **Best Practice**: Let model use its default
- **Note**: Combined with max_tokens issues, minimal configuration is preferred

## Implementation Strategy

### ❌ Previous Approach (Problematic)

```python
# .env file
LLM_TEMPERATURE=0.7  # Global setting

# Config class
def llm_temperature(self):
    return float(os.getenv('LLM_TEMPERATURE', 0.8))

# Usage
temperature = config.llm_temperature()  # Always uses global
```

**Problems**:
1. Breaks o3 models completely
2. Forces same temperature across all models
3. Overrides optimal model defaults

### ✅ Current Approach (Recommended)

```python
# .env file
# NO temperature setting - removed entirely

# LLM Provider
def generate(self, messages, **kwargs):
    params = {'model': self.model}
    
    # Only add temperature if explicitly provided
    if 'temperature' in kwargs:
        params['temperature'] = kwargs['temperature']
    
    # Special handling for o3 models
    if self.model.startswith('o3'):
        params.pop('temperature', None)  # Remove if present
    
    return client.chat.completions.create(messages=messages, **params)

# RAG Engine
def generate_answer(self, question, context, temperature=None):
    kwargs = {}
    if temperature is not None:
        kwargs['temperature'] = temperature
    # Let model use default if not specified
```

**Benefits**:
1. Compatible with all models (including o3)
2. Respects model-specific optimal defaults
3. Allows per-request customization
4. Prevents configuration errors

## Migration Guide

### Step 1: Remove Global Settings

```bash
# Remove from .env files
# DELETE: LLM_TEMPERATURE=0.7

# Remove from configuration classes
# DELETE: def llm_temperature(self): ...
```

### Step 2: Update Provider Code

Ensure providers only use temperature when explicitly provided:

```python
# Only add temperature if in kwargs
if 'temperature' in kwargs:
    config['temperature'] = kwargs['temperature']
```

### Step 3: Handle Model Exceptions

```python
# Remove temperature for models that don't support it
if model.startswith('o3'):
    params.pop('temperature', None)
```

## Use Cases

### When to Override Temperature

1. **Deterministic Tasks** (temperature=0.0):
   - Code generation
   - Factual Q&A
   - Data extraction

2. **Creative Tasks** (temperature=1.2-1.5):
   - Story generation
   - Brainstorming
   - Creative writing

3. **Balanced Tasks** (use defaults):
   - RAG applications
   - General chat
   - Most use cases

### RAG-Specific Recommendations

For RAG pipelines, model defaults are typically optimal:
- **Retrieval**: Not affected by temperature
- **Generation**: Default balances accuracy and naturalness
- **Override only if**: Users report too repetitive or too random

## Testing Considerations

### Verify Compatibility

```python
# Test each provider
providers = ['openai', 'gemini']
for provider in providers:
    # Test without temperature (should work for all)
    result = rag_engine.ask("Test question", provider=provider)
    
    # Test with temperature (should work except o3)
    if not provider.startswith('o3'):
        result = rag_engine.ask("Test question", temperature=0.5, provider=provider)
```

### Error Handling

Gracefully handle temperature-related errors:

```python
try:
    response = llm_provider.generate(messages, temperature=0.7)
except APIError as e:
    if "temperature" in str(e):
        # Retry without temperature
        response = llm_provider.generate(messages)
    else:
        raise
```

## Summary of Best Practices

1. **Remove all global temperature settings**
2. **Use model defaults by default**
3. **Only override for specific use cases**
4. **Never pass temperature to o3 models**
5. **Test thoroughly with each provider**
6. **Document any temperature overrides**

## Future Considerations

As models evolve:
- More models may drop temperature support (like o3)
- New parameters may replace temperature
- Model-specific optimizations may make overrides unnecessary

**Recommendation**: Minimize configuration, maximize compatibility.

---

*Document created: January 2025*  
*Last updated: January 10, 2025*  
*Research basis: OpenAI API testing, Multi-provider implementation experience*