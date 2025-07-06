# Model Strategy for RAG Systems: A Flexible Experimentation Framework

## Executive Summary

This document outlines a comprehensive strategy for model selection and experimentation in RAG (Retrieval-Augmented Generation) systems, based on learnings from implementing with OpenAI's o3 model and understanding the fundamental differences between reasoning and generative models. We propose a flexible, configuration-driven architecture that enables easy model switching, stage-specific optimization, and systematic experimentation.

## Table of Contents

1. [Key Learnings: o3 vs Generative Models](#key-learnings-o3-vs-generative-models)
2. [Conceptual Framework for Model Selection](#conceptual-framework-for-model-selection)
3. [Flexible Model Experimentation System Design](#flexible-model-experimentation-system-design)
4. [Implementation Approaches](#implementation-approaches)
5. [Migration Strategy](#migration-strategy)
6. [Future Considerations](#future-considerations)

## Key Learnings: o3 vs Generative Models

### The o3 Experience

Our implementation with OpenAI's o3 model revealed fundamental differences between reasoning and generative models:

1. **Model Type Mismatch**
   - o3 is a **reasoning model** optimized for complex problem-solving
   - RAG typically needs **generative models** for natural language synthesis
   - Using o3 for simple Q&A is like using a supercomputer for word processing

2. **Technical Constraints**
   - No temperature parameter support (fixed at 1)
   - Occasional empty responses on straightforward queries
   - Higher latency due to internal reasoning chains
   - Significantly higher cost per token

3. **Task Alignment**
   - **Good for o3**: Complex analysis, multi-step reasoning, code generation
   - **Poor for o3**: Simple Q&A, summarization, creative writing
   - **Optimal**: Using task-appropriate models for each pipeline stage

### Model Categories and Use Cases

| Model Type | Characteristics | Best Use Cases | Example Models |
|------------|----------------|----------------|----------------|
| **Reasoning** | Deep analysis, step-by-step thinking | Complex queries, fact checking | o3, o1-preview |
| **Generative** | Fast, creative, conversational | Q&A, summarization, chat | GPT-4, Claude-3 |
| **Embedding** | Vector representations | Semantic search, retrieval | text-embedding-3-small |
| **Specialized** | Task-specific optimization | Classification, NER | BERT variants |

## Conceptual Framework for Model Selection

### The RAG Pipeline Stages

A typical RAG pipeline has distinct stages, each with different model requirements:

```
Query → [Embedding] → Vector Search → [Reranking] → Context Assembly → [Generation] → Response
         ↓                             ↓                                ↓
    Embedding Model              Reranking Model                   Generation Model
```

### Model Selection Criteria

1. **Task Complexity**
   - Simple factual retrieval → Lightweight generative model
   - Complex reasoning → Reasoning model
   - Semantic matching → Specialized embedding model

2. **Performance Requirements**
   - Real-time chat → Fast generative models
   - Batch processing → Can use slower, more accurate models
   - Cost-sensitive → Smaller, efficient models

3. **Quality Expectations**
   - Production customer-facing → High-quality models
   - Internal testing → Cost-effective models
   - Research/experimentation → Varied models for comparison

### The Optimal Model Mix

```yaml
# Example: Financial Analysis RAG
embedding: text-embedding-3-small      # Fast, accurate semantic search
reranking: cohere-rerank-english-v2.0  # Specialized reranking
simple_qa: gpt-4-turbo                  # Fast, conversational
complex_analysis: o3-mini               # Deep reasoning when needed
summarization: claude-3-haiku           # Cost-effective summaries
```

## Flexible Model Experimentation System Design

### Architecture Overview

```
┌─────────────────┐
│  Configuration  │
│   (YAML/JSON)   │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Model   │
    │Registry │
    └────┬────┘
         │
┌────────▼────────┐     ┌─────────────┐
│ Model Selector  │────▶│   Metrics   │
│    (Router)     │     │  Collector  │
└────────┬────────┘     └─────────────┘
         │
    ┌────▼────┐
    │Pipeline │
    │ Stages  │
    └─────────┘
```

### Core Components

1. **Model Registry**: Centralized definition of available models
2. **Model Selector**: Routes requests to appropriate models
3. **Configuration System**: Declarative model assignment
4. **Metrics Collector**: Tracks performance, cost, and quality
5. **Pipeline Integration**: Seamless model switching per stage

### Configuration Schema

```yaml
# model-config.yaml
models:
  # Model definitions with capabilities
  openai-gpt4:
    provider: openai
    model_id: gpt-4-0125-preview
    capabilities: [chat, qa, summarization]
    cost_per_1k_tokens: { input: 0.01, output: 0.03 }
    max_tokens: 128000
    supports_temperature: true
    
  openai-o3:
    provider: openai
    model_id: o3-2025-01-17
    capabilities: [reasoning, analysis, code]
    cost_per_1k_tokens: { input: 0.05, output: 0.15 }
    max_tokens: 100000
    supports_temperature: false
    
  claude-3-opus:
    provider: anthropic
    model_id: claude-3-opus-20240229
    capabilities: [chat, qa, summarization, analysis]
    cost_per_1k_tokens: { input: 0.015, output: 0.075 }
    max_tokens: 200000
    supports_temperature: true

# Pipeline configuration
pipeline:
  default_model: openai-gpt4
  
  stages:
    embedding:
      model: openai-text-embedding-3-small
      
    simple_qa:
      model: openai-gpt4
      temperature: 0.7
      max_tokens: 1000
      
    complex_reasoning:
      model: openai-o3
      # No temperature (not supported)
      max_tokens: 4000
      
    summarization:
      model: claude-3-haiku
      temperature: 0.3
      max_tokens: 500

# Routing rules
routing:
  - condition: "query_complexity > 0.8"
    model: openai-o3
  - condition: "requires_sources"
    model: openai-gpt4
  - condition: "chat_mode"
    model: claude-3-opus
```

## Implementation Approaches

### 1. Model Registry Implementation

```python
# src/model_registry.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class ModelCapabilities:
    supports_temperature: bool
    supports_streaming: bool
    max_tokens: int
    capabilities: List[str]
    cost_per_1k_input: float
    cost_per_1k_output: float

class ModelProvider(ABC):
    @abstractmethod
    def create_llm(self, model_id: str, **kwargs):
        pass
    
    @abstractmethod
    def get_capabilities(self, model_id: str) -> ModelCapabilities:
        pass

class ModelRegistry:
    def __init__(self):
        self.providers: Dict[str, ModelProvider] = {}
        self.models: Dict[str, dict] = {}
    
    def register_provider(self, name: str, provider: ModelProvider):
        self.providers[name] = provider
    
    def register_model(self, model_id: str, config: dict):
        self.models[model_id] = config
    
    def get_model(self, model_id: str, **kwargs):
        config = self.models[model_id]
        provider = self.providers[config['provider']]
        
        # Apply model-specific constraints
        capabilities = provider.get_capabilities(config['model_id'])
        if not capabilities.supports_temperature and 'temperature' in kwargs:
            kwargs.pop('temperature')
            
        return provider.create_llm(config['model_id'], **kwargs)
```

### 2. Model Selector with Routing

```python
# src/model_selector.py
from typing import Optional, Dict, Any
import re

class ModelSelector:
    def __init__(self, config: dict, registry: ModelRegistry):
        self.config = config
        self.registry = registry
        self.metrics_collector = MetricsCollector()
    
    def select_model(self, 
                    stage: str, 
                    query: Optional[str] = None,
                    context: Optional[Dict[str, Any]] = None) -> Any:
        """Select appropriate model based on stage and context."""
        
        # Check for stage-specific configuration
        if stage in self.config['pipeline']['stages']:
            model_config = self.config['pipeline']['stages'][stage]
            model_id = model_config['model']
        else:
            # Apply routing rules
            model_id = self._apply_routing_rules(query, context)
        
        # Get model with configuration
        model = self.registry.get_model(
            model_id,
            **model_config.get('parameters', {})
        )
        
        # Wrap with metrics collection
        return MetricsWrapper(model, model_id, self.metrics_collector)
    
    def _apply_routing_rules(self, query: str, context: dict) -> str:
        """Apply routing rules to select model."""
        for rule in self.config.get('routing', []):
            if self._evaluate_condition(rule['condition'], query, context):
                return rule['model']
        
        return self.config['pipeline']['default_model']
    
    def _evaluate_condition(self, condition: str, query: str, context: dict) -> bool:
        """Evaluate routing condition."""
        # Simple implementation - can be extended
        if condition == "query_complexity > 0.8":
            return self._calculate_complexity(query) > 0.8
        elif condition == "requires_sources":
            return "source" in query.lower() or "cite" in query.lower()
        elif condition == "chat_mode":
            return context.get('mode') == 'chat'
        return False
```

### 3. Pipeline Integration

```python
# src/agent_qa_flexible.py
from langchain.chains import RetrievalQA
from langchain.memory import ConversationBufferMemory

class FlexibleAgentQA(AgentBase):
    def __init__(self, model_selector: ModelSelector, embeddings=None):
        super().__init__(embeddings)
        self.model_selector = model_selector
        self.memory = ConversationBufferMemory()
    
    def get_chain(self, query: str, **kwargs):
        """Get appropriate chain based on query analysis."""
        
        # Analyze query complexity
        complexity = self._analyze_query(query)
        
        # Select model based on complexity and context
        context = {
            'complexity': complexity,
            'mode': kwargs.get('mode', 'qa'),
            'has_memory': len(self.memory.chat_memory.messages) > 0
        }
        
        llm = self.model_selector.select_model('qa', query, context)
        
        # Build chain with selected model
        chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type=kwargs.get('chain_type', 'stuff'),
            retriever=self.get_retriever(**kwargs),
            return_source_documents=True,
            chain_type_kwargs={
                'prompt': self.get_prompt(kwargs.get('prompt_key', 'base')),
                'memory': self.memory if kwargs.get('use_memory') else None
            }
        )
        
        return chain
    
    def query(self, query: str, **kwargs):
        """Execute query with flexible model selection."""
        start_time = time.time()
        
        # Get appropriate chain
        chain = self.get_chain(query, **kwargs)
        
        # Execute query
        result = chain.invoke({"query": query})
        
        # Log metrics
        self.model_selector.metrics_collector.record(
            model_id=chain.llm.model_name,
            duration=time.time() - start_time,
            tokens_used=result.get('token_count', 0),
            stage='qa',
            success=bool(result.get('result'))
        )
        
        return result
```

### 4. Configuration Loader

```python
# src/config_loader.py
import yaml
from pathlib import Path

class ModelConfigLoader:
    def __init__(self, config_path: str = "model-config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Load and validate configuration."""
        with open(self.config_path) as f:
            config = yaml.safe_load(f)
        
        # Validate configuration
        self._validate_config(config)
        
        # Apply environment overrides
        config = self._apply_env_overrides(config)
        
        return config
    
    def _validate_config(self, config: dict):
        """Validate configuration schema."""
        required_keys = ['models', 'pipeline']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration key: {key}")
    
    def _apply_env_overrides(self, config: dict) -> dict:
        """Apply environment variable overrides."""
        import os
        
        # Example: MODEL_OVERRIDE_QA=claude-3-opus
        for key, value in os.environ.items():
            if key.startswith('MODEL_OVERRIDE_'):
                stage = key.replace('MODEL_OVERRIDE_', '').lower()
                if 'stages' not in config['pipeline']:
                    config['pipeline']['stages'] = {}
                config['pipeline']['stages'][stage] = {'model': value}
        
        return config
```

## Migration Strategy

### Phase 1: Compatibility Layer (Week 1)

```python
# src/agent_qa_compat.py
class AgentQACompat(AgentQA):
    """Compatibility wrapper for existing code."""
    
    def __init__(self, embeddings=None, llm=None):
        super().__init__(embeddings)
        
        # Create model selector with single model
        if llm:
            # Legacy single-model mode
            self.model_selector = SingleModelSelector(llm)
        else:
            # New flexible mode
            config = ModelConfigLoader().config
            registry = create_default_registry()
            self.model_selector = ModelSelector(config, registry)
```

### Phase 2: Gradual Migration (Weeks 2-3)

1. **Update configuration files**
   ```yaml
   # rag-youtube.conf
   # Legacy configuration (still supported)
   llm=openai
   openai_model=gpt-4
   
   # New configuration (opt-in)
   model_config_file=model-config.yaml
   enable_flexible_models=true
   ```

2. **Migrate agent implementations**
   - Start with `AgentQA`
   - Add model selection logic
   - Maintain backwards compatibility

3. **Update tests**
   ```python
   # test/test_flexible_models.py
   def test_model_routing():
       """Test that complex queries route to reasoning models."""
       agent = FlexibleAgentQA(test_model_selector)
       
       simple_result = agent.query("What is the weather?")
       assert simple_result['model_used'] == 'gpt-4'
       
       complex_result = agent.query("Analyze the correlation between...")
       assert complex_result['model_used'] == 'o3'
   ```

### Phase 3: Full Migration (Week 4)

1. Remove compatibility layers
2. Update documentation
3. Migrate all configurations to new format

## Future Considerations

### 1. A/B Testing Framework

```yaml
# ab-testing.yaml
experiments:
  qa_model_comparison:
    variants:
      - name: control
        model: gpt-4
        weight: 0.5
      - name: treatment
        model: claude-3-opus
        weight: 0.5
    metrics: [response_time, user_satisfaction, cost]
    duration: 7_days
```

### 2. Cost Tracking and Optimization

```python
class CostOptimizer:
    def __init__(self, budget_per_day: float):
        self.budget = budget_per_day
        self.spent_today = 0.0
    
    def select_model(self, models: List[str], query: str) -> str:
        """Select model considering cost constraints."""
        if self.spent_today > self.budget * 0.9:
            # Switch to cheaper models when near budget
            return self.get_cheapest_capable_model(models, query)
        return self.get_best_model(models, query)
```

### 3. Performance Monitoring

```python
# Prometheus metrics example
from prometheus_client import Counter, Histogram, Gauge

model_requests = Counter('rag_model_requests_total', 
                        'Total model requests', 
                        ['model', 'stage'])
model_latency = Histogram('rag_model_latency_seconds',
                         'Model response latency',
                         ['model', 'stage'])
model_cost = Counter('rag_model_cost_dollars',
                    'Cumulative model cost',
                    ['model'])
```

### 4. Dynamic Model Loading

```python
class DynamicModelLoader:
    """Load models on-demand to reduce memory usage."""
    
    def __init__(self, cache_size: int = 3):
        self.cache = LRUCache(cache_size)
    
    def get_model(self, model_id: str):
        if model_id not in self.cache:
            model = self._load_model(model_id)
            self.cache[model_id] = model
        return self.cache[model_id]
```

### 5. Model Fallback Chains

```yaml
# Fallback configuration
fallback_chains:
  primary_qa:
    - openai-gpt4        # Primary
    - anthropic-claude   # First fallback
    - ollama-llama2      # Local fallback
    - cached_responses   # Ultimate fallback
```

## Conclusion

The shift from single-model to flexible multi-model RAG systems is essential for optimizing cost, performance, and quality. By implementing a configuration-driven architecture with proper abstractions, we can:

1. **Match models to tasks** - Use reasoning models for complex analysis, generative models for chat
2. **Optimize costs** - Route simple queries to cheaper models
3. **Improve quality** - Leverage each model's strengths
4. **Enable experimentation** - A/B test different models easily
5. **Future-proof the system** - Add new models without code changes

The key insight from our o3 experience is that there's no "best" model—only the best model for a specific task. A flexible architecture lets us leverage this insight systematically.

### Next Steps

1. Implement Phase 1 compatibility layer
2. Create `model-config.yaml` with current models
3. Add metrics collection
4. Begin gradual migration
5. Set up A/B testing infrastructure

This architecture positions us to adapt quickly as new models emerge and our understanding of optimal model selection deepens.