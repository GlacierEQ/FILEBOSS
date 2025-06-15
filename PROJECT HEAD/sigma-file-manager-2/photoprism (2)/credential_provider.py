import os
import logging
from typing import List

# --- Logger Configuration ---
# Set up a basic logger. In a larger application, you might want to configure this
# more extensively (e.g., in your main application entry point).
logger = logging.getLogger(__name__)
# To see logs, you might need to add a handler and set level, e.g.:
# logging.basicConfig(level=logging.INFO) # Or logging.DEBUG

# --- Core Credential Fetching Logic ---
def _get_env_var(var_name: str) -> str:
    """
    Internal helper function to retrieve an environment variable.

    Args:
        var_name: The name of the environment variable.

    Returns:
        The value of the environment variable.

    Raises:
        ValueError: If the environment variable is not set or is empty.
    """
    value = os.getenv(var_name)
    if not value:
        msg = f"Mandatory environment variable '{var_name}' is not set or is empty. Please ensure it is defined in your environment."
        logger.error(msg)
        raise ValueError(msg)
    # logger.debug(f"Successfully retrieved environment variable '{var_name}'.") # Use with caution if values are sensitive
    return value

# --- List of All Managed Environment Variables (for reference and testing) ---
# This list will be populated with all the environment variable names managed by this module.
MANAGED_ENV_VARS: List[str] = []

# --- Specific Credential Accessor Functions ---

# Note: For each function below, you will need to set the corresponding
# environment variable in your system or .env file.

# Example: For get_openai_photoprism_api_key(), set OPENAI_PHOTOPRISM_API_KEY=your_actual_key

def get_openai_photoprism_api_key() -> str:
    """Retrieves the OpenAI API Key for the PhotoPrism Project."""
    env_var = "OPENAI_PHOTOPRISM_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_openai_brains_project_api_key() -> str:
    """Retrieves the OpenAI API Key for the BraINS Project."""
    env_var = "OPENAI_BRAINS_PROJECT_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_google_gemini_api_key() -> str:
    """Retrieves the Google Gemini API Key."""
    env_var = "GOOGLE_GEMINI_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_neo4j_uri() -> str:
    """Retrieves the Neo4j URI."""
    env_var = "NEO4J_URI"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_neo4j_user() -> str:
    """Retrieves the Neo4j User."""
    env_var = "NEO4J_USER"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_neo4j_password() -> str:
    """Retrieves the Neo4j Password."""
    env_var = "NEO4J_PASSWORD"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_postgres_prisma_connection_string() -> str:
    """Retrieves the Postgres Prisma Connection String."""
    env_var = "POSTGRES_PRISMA_CONNECTION_STRING"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_mem_api_key() -> str:
    """Retrieves the Mem API Key."""
    env_var = "MEM_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_huggingface_read_key() -> str:
    """Retrieves the Hugging Face Read Key."""
    env_var = "HUGGINGFACE_READ_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_huggingface_write_key() -> str:
    """Retrieves the Hugging Face Write Key."""
    env_var = "HUGGINGFACE_WRITE_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_huggingface_general_token() -> str:
    """Retrieves a general Hugging Face API Token (hf_zQMZ...)."""
    env_var = "HUGGINGFACE_GENERAL_TOKEN"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_elevenlabs_api_key() -> str:
    """Retrieves the ElevenLabs API Key."""
    env_var = "ELEVENLABS_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_pinecone_env1_api_key() -> str:
    """Retrieves the Pinecone API Key for Environment 1."""
    env_var = "PINECONE_ENV1_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_pinecone_env2_api_key() -> str:
    """Retrieves the Pinecone API Key for Environment 2."""
    env_var = "PINECONE_ENV2_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_figma_api_key() -> str:
    """Retrieves the Figma API Key."""
    env_var = "FIGMA_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_perplexity_api_key() -> str:
    """Retrieves the Perplexity API Key."""
    env_var = "PERPLEXITY_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_taskade_api_key() -> str:
    """Retrieves the Taskade API Key."""
    env_var = "TASKADE_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_smitherai_api_key() -> str:
    """Retrieves the Smithery AI API Key."""
    env_var = "SMITHERAI_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_anthropic_api_key() -> str:
    """Retrieves the Anthropic API Key."""
    env_var = "ANTHROPIC_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_e2b_api_key() -> str:
    """Retrieves the E2B API Key."""
    env_var = "E2B_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_firebase_firecrawl_api_key() -> str:
    """Retrieves the Firebase/Firecrawl API Key."""
    env_var = "FIREBASE_FIRECRAWL_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_windsurf_auth_hi_guy_jwt() -> str:
    """Retrieves the JWT Token for Windsurf Auth (Hi Guy Reviews). Note: JWTs are often short-lived."""
    env_var = "WINDSURF_AUTH_HI_GUY_JWT"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_github_pat_awesome_forensics() -> str:
    """Retrieves the GitHub Personal Access Token for Awesome Forensics."""
    env_var = "GITHUB_PAT_AWESOME_FORENSICS"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_apryse_sdk_demo_key() -> str:
    """Retrieves the Apryse SDK Demo Key."""
    env_var = "APRYSE_SDK_DEMO_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_github_pat_generic1() -> str:
    """Retrieves a generic GitHub Personal Access Token (formerly 11BOJ6...RULJIUYW...)."""
    env_var = "GITHUB_PAT_GENERIC1"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_herd_trail_agent_jwt() -> str:
    """Retrieves the JWT for Herd Trail Agent Web Browser. Note: JWTs are often short-lived."""
    env_var = "HERD_TRAIL_AGENT_JWT"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_microsoft_tenant_association_jwt() -> str:
    """Retrieves the Microsoft Tenant Association JWT. Note: JWTs are often short-lived."""
    env_var = "MICROSOFT_TENANT_ASSOCIATION_JWT"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_supermemory_api_key() -> str:
    """Retrieves the Supermemory API Key."""
    env_var = "SUPERMEMORY_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_render_api_key() -> str:
    """Retrieves the Render API Key."""
    env_var = "RENDER_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_nebius_ai_studio_mixtral_jwt() -> str:
    """Retrieves the Nebius AI Studio (Mixtral) JWT. Note: JWTs are often short-lived."""
    env_var = "NEBIUS_AI_STUDIO_MIXTRAL_JWT"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_together_ai_api_key() -> str:
    """Retrieves the Together.ai API Key."""
    env_var = "TOGETHER_AI_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_cohere_api_key() -> str:
    """Retrieves the Cohere API Key."""
    env_var = "COHERE_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_github_pat_generic2() -> str:
    """Retrieves a generic GitHub Personal Access Token (formerly 11BOJ6...RULXVUR...)."""
    env_var = "GITHUB_PAT_GENERIC2"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_github_pat_omni_engine() -> str:
    """Retrieves the GitHub Personal Access Token for Omni_Engine (ghp_S41z...)."""
    env_var = "GITHUB_PAT_OMNI_ENGINE"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_github_pat_generic3() -> str:
    """Retrieves a generic GitHub Personal Access Token (formerly 11BOJ6...IXOUJLUT...)."""
    env_var = "GITHUB_PAT_GENERIC3"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_google_general_api_key() -> str:
    """Retrieves the Google (General) API Key."""
    env_var = "GOOGLE_GENERAL_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_natif_document_processing_api_key() -> str:
    """Retrieves the Natif Document Processing API Key."""
    env_var = "NATIF_DOCUMENT_PROCESSING_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_deepseek_api_key_1() -> str:
    """Retrieves the DeepSeek API Key (formerly sk-1720...)."""
    env_var = "DEEPSEEK_API_KEY_1"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_deepseek_api_key_2() -> str:
    """Retrieves the DeepSeek API Key (formerly sk-07c4...)."""
    env_var = "DEEPSEEK_API_KEY_2"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_deepseek_api_key_3() -> str:
    """Retrieves the DeepSeek API Key (formerly sk-4b3a...)."""
    env_var = "DEEPSEEK_API_KEY_3"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_openrouter_api_key_1() -> str:
    """Retrieves the OpenRouter API Key (formerly sk-or-v1-dfcb...)."""
    env_var = "OPENROUTER_API_KEY_1"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_openrouter_api_key_2() -> str:
    """Retrieves the OpenRouter API Key (formerly sk-or-v1-fff1...)."""
    env_var = "OPENROUTER_API_KEY_2"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_openrouter_management_api_key() -> str:
    """Retrieves the OpenRouter Management API Key (sk-or-adm...)."""
    env_var = "OPENROUTER_MANAGEMENT_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_langchain_langsmith_api_key() -> str:
    """Retrieves the LangChain/Langsmith API Key (Note: current value is a placeholder)."""
    env_var = "LANGCHAIN_LANGSMITH_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_postman_api_key() -> str:
    """Retrieves the Postman API Key."""
    env_var = "POSTMAN_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_snyk_github_container_id() -> str:
    """Retrieves the Snyk GitHub Container ID."""
    env_var = "SNYK_GITHUB_CONTAINER_ID"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

def get_cody_sourcegraph_api_key() -> str:
    """Retrieves the Cody (Sourcegraph) API Key."""
    env_var = "CODY_SOURCEGRAPH_API_KEY"
    MANAGED_ENV_VARS.append(env_var)
    return _get_env_var(env_var)

# --- Utility function to list all expected environment variables ---
def get_all_managed_env_var_names() -> List[str]:
    """
    Returns a list of all environment variable names that this module expects to be set.
    This can be useful for checking if all required variables are present.
    It dedupes the MANAGED_ENV_VARS list which might get duplicates if functions are called multiple times before this one.
    """
    # Ensure all functions are called at least once conceptually to populate MANAGED_ENV_VARS,
    # or better, define this list statically if functions aren't always called.
    # For simplicity here, we assume they might be populated dynamically by calls.
    # A more robust way is to define the list of env_vars statically alongside function definitions.
    # However, for this dynamic append approach, we just return the unique list.
    unique_vars = sorted(list(set(MANAGED_ENV_VARS)))
    if not unique_vars: # Fallback if no functions were called before this
        # This is a manual list, keep it updated if you add/remove functions!
        return sorted([
            "OPENAI_PHOTOPRISM_API_KEY", "OPENAI_BRAINS_PROJECT_API_KEY", "GOOGLE_GEMINI_API_KEY",
            "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "POSTGRES_PRISMA_CONNECTION_STRING",
            "MEM_API_KEY", "HUGGINGFACE_READ_KEY", "HUGGINGFACE_WRITE_KEY", "HUGGINGFACE_GENERAL_TOKEN",
            "ELEVENLABS_API_KEY", "PINECONE_ENV1_API_KEY", "PINECONE_ENV2_API_KEY", "FIGMA_API_KEY",
            "PERPLEXITY_API_KEY", "TASKADE_API_KEY", "SMITHERAI_API_KEY", "ANTHROPIC_API_KEY",
            "E2B_API_KEY", "FIREBASE_FIRECRAWL_API_KEY", "WINDSURF_AUTH_HI_GUY_JWT",
            "GITHUB_PAT_AWESOME_FORENSICS", "APRYSE_SDK_DEMO_KEY", "GITHUB_PAT_GENERIC1",
            "HERD_TRAIL_AGENT_JWT", "MICROSOFT_TENANT_ASSOCIATION_JWT", "SUPERMEMORY_API_KEY",
            "RENDER_API_KEY", "NEBIUS_AI_STUDIO_MIXTRAL_JWT", "TOGETHER_AI_API_KEY", "COHERE_API_KEY",
            "GITHUB_PAT_GENERIC2", "GITHUB_PAT_OMNI_ENGINE", "GITHUB_PAT_GENERIC3",
            "GOOGLE_GENERAL_API_KEY", "NATIF_DOCUMENT_PROCESSING_API_KEY", "DEEPSEEK_API_KEY_1",
            "DEEPSEEK_API_KEY_2", "DEEPSEEK_API_KEY_3", "OPENROUTER_API_KEY_1", "OPENROUTER_API_KEY_2",
            "OPENROUTER_MANAGEMENT_API_KEY", "LANGCHAIN_LANGSMITH_API_KEY", "POSTMAN_API_KEY",
            "SNYK_GITHUB_CONTAINER_ID", "CODY_SOURCEGRAPH_API_KEY"
        ])
    return unique_vars

# --- Example Usage (for testing or demonstration) ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger.info("Attempting to access credentials...")
    logger.info("This script provides functions to access various API keys and tokens from environment variables.")
    logger.info("Ensure the corresponding environment variables are set before running.")

    expected_vars = get_all_managed_env_var_names()
    logger.info(f"\nThis module manages {len(expected_vars)} credentials tied to the following environment variables:")
    for var_name in expected_vars:
        logger.info(f"  - {var_name}")

    logger.info("\nExample: Trying to fetch 'OPENAI_PHOTOPRISM_API_KEY' (will fail if not set).")
    try:
        key = get_openai_photoprism_api_key()
        logger.info(f"Successfully fetched OPENAI_PHOTOPRISM_API_KEY: {key[:5]}... (partially masked for safety)")
    except ValueError as e:
        logger.error(f"Error fetching OPENAI_PHOTOPRISM_API_KEY: {e}")

    logger.info("\nTo use this module in your other scripts:")
    logger.info("1. Ensure this file (credential_provider.py) is in your Python path.")
    logger.info("2. Set the required environment variables (e.g., in a .env file and use python-dotenv, or set them system-wide).")
    logger.info("3. In your script, import specific functions: from credential_provider import get_your_desired_key")
    logger.info("   Example: my_key = get_figma_api_key()")
