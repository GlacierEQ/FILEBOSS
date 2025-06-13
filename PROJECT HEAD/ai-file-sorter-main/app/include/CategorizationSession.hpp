#ifndef CATEGORIZATIONSESSION_HPP
#define CATEGORIZATIONSESSION_HPP

#include <LLMClient.hpp>
#include <string>

class CategorizationSession {
    std::string key;

public:
    CategorizationSession();
    ~CategorizationSession();

    LLMClient create_llm_client() const;
};

#endif