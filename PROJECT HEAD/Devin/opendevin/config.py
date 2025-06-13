import os

import argparse
import toml
from dotenv import load_dotenv

from opendevin.schema import ConfigType

load_dotenv()

DEFAULT_CONFIG: dict = {
    # Legacy LLM configurations
    ConfigType.LLM_API_KEY: None,
    ConfigType.LLM_BASE_URL: None,
    ConfigType.LLM_MODEL: 'gpt-3.5-turbo-1106',
    ConfigType.LLM_EMBEDDING_MODEL: 'local',
    ConfigType.LLM_DEPLOYMENT_NAME: None,
    ConfigType.LLM_API_VERSION: None,
    ConfigType.LLM_NUM_RETRIES: 1,
    ConfigType.LLM_COOLDOWN_TIME: 1,
    
    # Multi-LLM Provider configurations
    ConfigType.LLM_ROUTING_ENABLED: 'true',
    ConfigType.LLM_AUTO_SELECTION: 'true',
    ConfigType.LLM_FALLBACK_ENABLED: 'true',
    ConfigType.LLM_COST_OPTIMIZATION: 'true',
    ConfigType.LLM_PERFORMANCE_PREFERENCE: '0.7',
    
    # Provider-specific API keys
    ConfigType.OPENAI_API_KEY: None,
    ConfigType.ANTHROPIC_API_KEY: None,
    ConfigType.DEEPSEEK_API_KEY: None,
    ConfigType.OPENROUTER_API_KEY: None,
    ConfigType.COHERE_API_KEY: None,
    ConfigType.TOGETHER_API_KEY: None,
    ConfigType.NEBIUS_API_KEY: None,
    
    # Workspace configurations
    ConfigType.WORKSPACE_BASE: os.getcwd(),
    ConfigType.WORKSPACE_MOUNT_PATH: None,
    ConfigType.WORKSPACE_MOUNT_REWRITE: None,
    
    # Sandbox configurations
    ConfigType.SANDBOX_CONTAINER_IMAGE: 'ghcr.io/opendevin/sandbox',
    ConfigType.SANDBOX_TYPE: 'ssh',
    
    # Agent configurations
    ConfigType.RUN_AS_DEVIN: 'true',
    ConfigType.AGENT: 'MonologueAgent',
    ConfigType.MAX_ITERATIONS: 100,
    # GPT-4 pricing is $10 per 1M input tokens. Since tokenization happens on LLM side,
    # we cannot easily count number of tokens, but we can count characters.
    # Assuming 5 characters per token, 5 million is a reasonable default limit.
    ConfigType.MAX_CHARS: 5_000_000,
    
    # Network configurations
    ConfigType.USE_HOST_NETWORK: 'false',
    ConfigType.SSH_HOSTNAME: 'localhost',
    
    # UI configurations
    ConfigType.DISABLE_COLOR: 'false',
    
    # Supabase integration
    ConfigType.SUPABASE_URL: None,
    ConfigType.SUPABASE_ANON_KEY: None,
    ConfigType.SUPABASE_SERVICE_ROLE_KEY: None,
    
    # Memory system configurations
    ConfigType.MEMORY_ENABLED: 'true',
    ConfigType.MEMORY_PROVIDER: 'hybrid',
    ConfigType.MAX_MEMORY_ITEMS: 10000,
    ConfigType.MEMORY_PERSISTENCE: 'true',
    ConfigType.SESSION_MEMORY_ENABLED: 'true',
    ConfigType.CROSS_SESSION_MEMORY: 'true',
    ConfigType.MEMORY_CONSOLIDATION_THRESHOLD: 1000,
    
    # Mem0 configurations
    ConfigType.MEM0_API_KEY: None,
    ConfigType.MEM0_ORG_ID: None,
    ConfigType.MEM0_PROJECT_ID: None,
    
    # Memory storage configurations
    ConfigType.REDIS_URL: 'redis://localhost:6379',
    ConfigType.SQLITE_PATH: './data/memory.db',
    
    # Memory embedding configurations
    ConfigType.MEMORY_EMBEDDING_MODEL: 'BAAI/bge-small-en-v1.5',
    ConfigType.MEMORY_EMBEDDING_DIMENSION: 384,
    ConfigType.MEMORY_CHUNK_SIZE: 512,
    ConfigType.MEMORY_CHUNK_OVERLAP: 50,
    
    # Memory search configurations
    ConfigType.MEMORY_SIMILARITY_THRESHOLD: 0.7,
    ConfigType.MEMORY_MAX_RESULTS: 10,
    ConfigType.MEMORY_USE_HYBRID_SEARCH: 'true',
    ConfigType.MEMORY_RERANK_RESULTS: 'true',
    
    # Memory plugin configurations
    ConfigType.MEMORY_AUTO_SUMMARIZATION: 'true',
    ConfigType.MEMORY_CONTEXTUAL_RECALL: 'true',
    ConfigType.MEMORY_LEARNING_ADAPTATION: 'true',
    ConfigType.MEMORY_CONSOLIDATION: 'true'}]}],
}

config_str = ''
if os.path.exists('config.toml'):
    with open('config.toml', 'rb') as f:
        config_str = f.read().decode('utf-8')

tomlConfig = toml.loads(config_str)
config = DEFAULT_CONFIG.copy()
for k, v in config.items():
    if k in os.environ:
        config[k] = os.environ[k]
    elif k in tomlConfig:
        config[k] = tomlConfig[k]


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Run an agent with a specific task')
    parser.add_argument(
        '-d',
        '--directory',
        type=str,
        help='The working directory for the agent',
    )
    args, _ = parser.parse_known_args()
    if args.directory:
        config[ConfigType.WORKSPACE_BASE] = os.path.abspath(args.directory)
        print(f'Setting workspace base to {config[ConfigType.WORKSPACE_BASE]}')


parse_arguments()


def finalize_config():
    if config.get(ConfigType.WORKSPACE_MOUNT_REWRITE) and not config.get(ConfigType.WORKSPACE_MOUNT_PATH):
        base = config.get(ConfigType.WORKSPACE_BASE) or os.getcwd()
        parts = config[ConfigType.WORKSPACE_MOUNT_REWRITE].split(':')
        config[ConfigType.WORKSPACE_MOUNT_PATH] = base.replace(parts[0], parts[1])


finalize_config()


def get(key: str, required: bool = False):
    """
    Get a key from the environment variables or config.toml or default configs.
    """
    value = config.get(key)
    if not value and required:
        raise KeyError(f"Please set '{key}' in `config.toml` or `.env`.")
    return value
