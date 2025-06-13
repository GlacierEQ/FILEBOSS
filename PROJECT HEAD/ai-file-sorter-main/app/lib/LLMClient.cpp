#include "LLMClient.hpp"
#include "Types.hpp"
#include "Utils.hpp"
#include <curl/curl.h>
#include <glib.h>
#include <filesystem>
#ifdef _WIN32
    #include <json/json.h>
#elif __APPLE__
    #include <json/json.h>
#else
    #include <jsoncpp/json/json.h>
#endif

#include <iostream>
#include <sstream>


// Helper function to write the response from curl into a string
static size_t WriteCallback(void *contents, size_t size, size_t nmemb, std::string *response)
{
    size_t totalSize = size * nmemb;
    response->append((char *)contents, totalSize);
    return totalSize;
}


LLMClient::LLMClient(const std::string &api_key) : api_key(api_key)
{}


std::string LLMClient::send_api_request(std::string json_payload) {
    CURL *curl;
    CURLcode res;
    std::string response_string;
    std::string api_url = "https://api.openai.com/v1/chat/completions";

    curl = curl_easy_init();
    if (!curl) {
        throw std::runtime_error("Initialization Error: Failed to initialize cURL.");
    }

    #ifdef _WIN32
        std::string cert_path = std::filesystem::current_path().string() + "\\certs\\cacert.pem";
        curl_easy_setopt(curl, CURLOPT_CAINFO, cert_path.c_str());
    #endif
    curl_easy_setopt(curl, CURLOPT_URL, api_url.c_str());
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);
    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    headers = curl_slist_append(headers, ("Authorization: Bearer " + api_key).c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_payload.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_string);

    res = curl_easy_perform(curl);

    if (res != CURLE_OK) {
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
        throw std::runtime_error("Network Error: " + std::string(curl_easy_strerror(res)));
    }

    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
    curl_easy_cleanup(curl);
    curl_slist_free_all(headers);

    Json::CharReaderBuilder reader_builder;
    Json::Value root;
    std::istringstream response_stream(response_string);
    std::string errors;
    
    if (!Json::parseFromStream(reader_builder, response_stream, &root, &errors)) {
        throw std::runtime_error("Response Error: Failed to parse JSON response. " + errors);
    }

    if (http_code == 401) {
        throw std::runtime_error("Authentication Error: Invalid or missing API key.");
    } else if (http_code == 403) {
        throw std::runtime_error("Authorization Error: API key does not have sufficient permissions.");
    } else if (http_code >= 500) {
        throw std::runtime_error("Server Error: OpenAI server returned an error. Status code: " + std::to_string(http_code));
    } else if (http_code >= 400) {
        std::string error_message = root["error"]["message"].asString();
        throw std::runtime_error("Client Error: " + error_message);
    }

    std::string category = root["choices"][0]["message"]["content"].asString();
    return category;
}


std::string LLMClient::categorize_file(const std::string& file_name, FileType file_type)
{
    std::string json_payload = make_payload(file_name, file_type);

    return send_api_request(json_payload);
}


std::string LLMClient::make_payload(const std::string& file_name, const FileType file_type)
{
    std::string prompt;

    if (file_type == FileType::File) {
        // g_print("File name: %s\n", file_name.c_str());
        prompt = "Categorize file: " + file_name;
    } else {
        // g_print("Directory name: %s\n", file_name.c_str());
        prompt = "Categorize directory: " + file_name;
    }

    std::string json_payload = R"(
    {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a file categorization assistant. If it's an installer, give what category the software falls into after installation. Category must be relevant to file extension general type (e.g., PDF, MD, TXT files have one general type). Always return the category of a file or directory name in one or two words, plural. Also give subcategory where appropriate. Subcategory must be relevant to probable file contents. The format is Category : Subcategory."},
            {"role": "user", "content": ")" + prompt + R"("}
        ]
    })";
    
    return json_payload;
}