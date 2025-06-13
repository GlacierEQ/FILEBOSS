"""
LLM Router Module for Multi-Provider Integration

This module provides intelligent routing logic to automatically select
the best LLM model for each request based on task type, cost, performance,
and provider availability.
"""

import os
import json
import time
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import toml
from opendevin.logger import opendevin_logger
from opendevin import config


class TaskType(str, Enum):
    """Task types for model selection."""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    GENERAL_CHAT = "general_chat"
    ANALYSIS = "analysis"
    REASONING = "reasoning"
    MATH = "math"
    WRITING = "writing"
    SEARCH_RAG = "search_rag"
    TRANSLATION = "translation"
    DEBUG = "debug"
    SUMMARIZATION = "summarization"
    DATA_ANALYSIS = "data_analysis"


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    enabled: bool
    api_key: Optional[str]
    base_url: str
    models: List[str]
    priority: int
    cost_per_1k_tokens: Dict[str, float]
    max_tokens: int
    strengths: List[str]
    current_failures: int = 0
    last_failure_time: Optional[float] = None
    total_requests: int = 0
    successful_requests: int = 0
    average_response_time: float = 0.0

    @property
    def reliability_score(self) -> float:
        """Calculate reliability score based on success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def is_available(self) -> bool:
        """Check if provider is available (not in failure state)."""
        if not self.enabled or not self.api_key:
            return False
        
        # If there have been recent failures, check if cooldown period has passed
        if self.current_failures > 0 and self.last_failure_time:
            cooldown_period = min(300, self.current_failures * 60)  # Max 5 min cooldown
            if time.time() - self.last_failure_time < cooldown_period:
                return False
        
        return True

    def record_success(self, response_time: float):
        """Record a successful request."""
        self.total_requests += 1
        self.successful_requests += 1
        self.current_failures = 0
        self.last_failure_time = None
        
        # Update rolling average response time
        if self.average_response_time == 0:
            self.average_response_time = response_time
        else:
            self.average_response_time = (self.average_response_time * 0.9) + (response_time * 0.1)

    def record_failure(self):
        """Record a failed request."""
        self.total_requests += 1
        self.current_failures += 1
        self.last_failure_time = time.time()


class LLMRouter:
    """Intelligent LLM router for multi-provider integration."""
    
    def __init__(self, config_path: str = "warp.toml"):
        self.providers: Dict[str, ProviderConfig] = {}
        self.task_preferences: Dict[TaskType, List[str]] = {}
        self.quality_tiers: Dict[str, List[str]] = {}
        self.routing_config = {
            'auto_selection': True,
            'fallback_enabled': True,
            'cost_optimization': True,
            'performance_preference': 0.7,
            'load_balancing': True
        }
        self._load_config(config_path)
        
    def _load_config(self, config_path: str):
        """Load configuration from warp.toml file."""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = toml.load(f)
                    
                # Load provider configurations
                providers_config = config_data.get('integrations', {}).get('llm_providers', {})
                for provider_name, provider_data in providers_config.items():
                    if provider_data.get('enabled', False):
                        api_key = self._resolve_env_var(provider_data.get('api_key', ''))
                        if api_key or provider_name == 'ollama':  # Ollama doesn't need API key
                            self.providers[provider_name] = ProviderConfig(
                                name=provider_name,
                                enabled=provider_data.get('enabled', False),
                                api_key=api_key,
                                base_url=provider_data.get('base_url', ''),
                                models=provider_data.get('models', []),
                                priority=provider_data.get('priority', 1),
                                cost_per_1k_tokens=provider_data.get('cost_per_1k_tokens', {'input': 0, 'output': 0}),
                                max_tokens=provider_data.get('max_tokens', 4096),
                                strengths=provider_data.get('strengths', [])
                            )
                
                # Load routing configuration
                routing_config = config_data.get('llm_routing', {})
                self.routing_config.update(routing_config)
                
                # Load task preferences
                task_prefs = routing_config.get('task_preferences', {})
                for task_name, models in task_prefs.items():
                    try:
                        task_type = TaskType(task_name)
                        self.task_preferences[task_type] = models
                    except ValueError:
                        opendevin_logger.warning(f"Unknown task type: {task_name}")
                
                # Load quality tiers
                self.quality_tiers = routing_config.get('quality_tiers', {})
                
            else:
                opendevin_logger.warning(f"Config file {config_path} not found, using defaults")
                self._load_default_config()
                
        except Exception as e:
            opendevin_logger.error(f"Error loading config: {e}")
            self._load_default_config()
    
    def _resolve_env_var(self, value: str) -> Optional[str]:
        """Resolve environment variable references in config values."""
        if value.startswith('${') and value.endswith('}'):
            env_var = value[2:-1]
            return os.getenv(env_var)
        return value if value else None
    
    def _load_default_config(self):
        """Load default configuration when config file is not available."""
        # Add basic OpenAI configuration if API key is available
        openai_key = config.get('OPENAI_API_KEY')
        if openai_key:
            self.providers['openai'] = ProviderConfig(
                name='openai',
                enabled=True,
                api_key=openai_key,
                base_url='https://api.openai.com/v1',
                models=['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
                priority=10,
                cost_per_1k_tokens={'input': 0.01, 'output': 0.03},
                max_tokens=128000,
                strengths=['general', 'coding', 'reasoning']
            )
        
        # Add Ollama if available locally
        self.providers['ollama'] = ProviderConfig(
            name='ollama',
            enabled=True,
            api_key='ollama',
            base_url='http://localhost:11434',
            models=['llama3.1:8b', 'codellama:7b-instruct'],
            priority=3,
            cost_per_1k_tokens={'input': 0.0, 'output': 0.0},
            max_tokens=32000,
            strengths=['local', 'privacy', 'cost-free']
        )
    
    def select_model(self, 
                    task_type: Optional[TaskType] = None,
                    context_length: int = 0,
                    prefer_cost: bool = False,
                    exclude_providers: List[str] = None) -> Tuple[str, str, ProviderConfig]:
        """
        Select the best model for a given task.
        
        Args:
            task_type: The type of task being performed
            context_length: Expected context length in tokens
            prefer_cost: Whether to prioritize cost over performance
            exclude_providers: List of provider names to exclude
            
        Returns:
            Tuple of (model_name, provider_name, provider_config)
        """
        exclude_providers = exclude_providers or []
        
        # Filter available providers
        available_providers = {
            name: provider for name, provider in self.providers.items()
            if provider.is_available and name not in exclude_providers
        }
        
        if not available_providers:
            raise Exception("No available LLM providers")
        
        # Get candidate models based on task preferences
        candidate_models = self._get_candidate_models(task_type, available_providers, context_length)
        
        if not candidate_models:
            # Fallback to any available model
            for provider in available_providers.values():
                if provider.models and context_length <= provider.max_tokens:
                    candidate_models.append((provider.models[0], provider.name, provider))
        
        if not candidate_models:
            raise Exception("No suitable models found for the given requirements")
        
        # Score and select the best model
        best_model = self._score_and_select_model(candidate_models, prefer_cost)
        
        opendevin_logger.info(f"Selected model: {best_model[0]} from provider: {best_model[1]}")
        return best_model
    
    def _get_candidate_models(self, 
                             task_type: Optional[TaskType],
                             available_providers: Dict[str, ProviderConfig],
                             context_length: int) -> List[Tuple[str, str, ProviderConfig]]:
        """Get candidate models based on task preferences."""
        candidates = []
        
        # If task type is specified, use task preferences
        if task_type and task_type in self.task_preferences:
            preferred_models = self.task_preferences[task_type]
            
            for model_name in preferred_models:
                # Check if model is available in any provider
                for provider_name, provider in available_providers.items():
                    if (model_name in provider.models and 
                        context_length <= provider.max_tokens):
                        candidates.append((model_name, provider_name, provider))
                        break
        
        # If no task-specific preferences or no matches, use all available models
        if not candidates:
            for provider_name, provider in available_providers.items():
                for model_name in provider.models:
                    if context_length <= provider.max_tokens:
                        candidates.append((model_name, provider_name, provider))
        
        return candidates
    
    def _score_and_select_model(self, 
                               candidates: List[Tuple[str, str, ProviderConfig]],
                               prefer_cost: bool = False) -> Tuple[str, str, ProviderConfig]:
        """Score candidate models and select the best one."""
        scored_candidates = []
        
        for model_name, provider_name, provider in candidates:
            score = self._calculate_model_score(model_name, provider, prefer_cost)
            scored_candidates.append((score, model_name, provider_name, provider))
        
        # Sort by score (higher is better)
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # If load balancing is enabled, add some randomness for similar scores
        if self.routing_config.get('load_balancing', True) and len(scored_candidates) > 1:
            # Group candidates with similar scores (within 10%)
            top_score = scored_candidates[0][0]
            similar_candidates = [
                c for c in scored_candidates 
                if c[0] >= top_score * 0.9
            ]
            
            if len(similar_candidates) > 1:
                selected = random.choice(similar_candidates)
                return (selected[1], selected[2], selected[3])
        
        # Return the top candidate
        return (scored_candidates[0][1], scored_candidates[0][2], scored_candidates[0][3])
    
    def _calculate_model_score(self, 
                              model_name: str, 
                              provider: ProviderConfig,
                              prefer_cost: bool = False) -> float:
        """Calculate a score for a model based on various factors."""
        score = 0.0
        
        # Base priority score
        score += provider.priority * 10
        
        # Reliability score
        score += provider.reliability_score * 20
        
        # Cost factor (lower cost = higher score when cost optimization is enabled)
        if self.routing_config.get('cost_optimization', True) or prefer_cost:
            total_cost = provider.cost_per_1k_tokens['input'] + provider.cost_per_1k_tokens['output']
            if total_cost == 0:  # Free models get bonus points
                score += 30
            else:
                # Inverse cost score (cheaper is better)
                score += max(0, 20 - (total_cost * 1000))  # Scale cost to reasonable range
        
        # Performance preference
        performance_weight = self.routing_config.get('performance_preference', 0.7)
        if performance_weight > 0.5:  # Prefer higher quality models
            # Check quality tier
            for tier_name, tier_models in self.quality_tiers.items():
                if model_name in tier_models:
                    if tier_name == 'tier1':
                        score += 25 * performance_weight
                    elif tier_name == 'tier2':
                        score += 15 * performance_weight
                    elif tier_name == 'tier3':
                        score += 10 * performance_weight
                    break
        
        # Response time factor (faster is better)
        if provider.average_response_time > 0:
            # Inverse response time (faster = higher score)
            time_score = max(0, 10 - provider.average_response_time)
            score += time_score
        
        # Recent failure penalty
        if provider.current_failures > 0:
            score -= provider.current_failures * 5
        
        return score
    
    def record_success(self, provider_name: str, response_time: float):
        """Record a successful request for performance tracking."""
        if provider_name in self.providers:
            self.providers[provider_name].record_success(response_time)
    
    def record_failure(self, provider_name: str):
        """Record a failed request for reliability tracking."""
        if provider_name in self.providers:
            self.providers[provider_name].record_failure()
    
    def get_fallback_models(self, 
                          exclude_providers: List[str],
                          context_length: int = 0) -> List[Tuple[str, str, ProviderConfig]]:
        """Get fallback models when primary selection fails."""
        if not self.routing_config.get('fallback_enabled', True):
            return []
        
        available_providers = {
            name: provider for name, provider in self.providers.items()
            if provider.is_available and name not in exclude_providers
        }
        
        fallback_candidates = []
        for provider_name, provider in available_providers.items():
            for model_name in provider.models:
                if context_length <= provider.max_tokens:
                    fallback_candidates.append((model_name, provider_name, provider))
        
        # Sort by reliability and priority
        fallback_candidates.sort(
            key=lambda x: (x[2].reliability_score, x[2].priority),
            reverse=True
        )
        
        return fallback_candidates[:3]  # Return top 3 fallback options
    
    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers."""
        stats = {}
        for name, provider in self.providers.items():
            stats[name] = {
                'enabled': provider.enabled,
                'available': provider.is_available,
                'total_requests': provider.total_requests,
                'successful_requests': provider.successful_requests,
                'reliability_score': provider.reliability_score,
                'average_response_time': provider.average_response_time,
                'current_failures': provider.current_failures,
                'models': provider.models,
                'priority': provider.priority
            }
        return stats


# Global router instance
_router_instance = None

def get_router() -> LLMRouter:
    """Get the global router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter()
    return _router_instance

def reset_router():
    """Reset the global router instance."""
    global _router_instance
    _router_instance = None

