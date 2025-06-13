#include "CategorizationSession.hpp"
#include "CryptoManager.hpp"
#include <stdexcept>
#include <iostream>
#include <algorithm> // For std::fill
#include <cstdlib>   // For std::getenv


CategorizationSession::CategorizationSession()
{
    const char* env_pc = std::getenv("ENV_PC");
    const char* env_rr = std::getenv("ENV_RR");

    if (!env_pc || !env_rr) {
        throw std::runtime_error("Missing environment variables for key decryption");
    }

    CryptoManager crypto(env_pc, env_rr);
    key = crypto.reconstruct();
}


CategorizationSession::~CategorizationSession()
{
    // Securely clear key memory
    std::fill(key.begin(), key.end(), '\0');
}


LLMClient CategorizationSession::create_llm_client() const
{
    return LLMClient(key);
}