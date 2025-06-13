#include "EmbeddedEnv.hpp"
#include <glib.h>
#include <sstream> 
#include <cstdlib>
#include <stdexcept>
#include <gio/gio.h>
extern GResource *resources_get_resource();


EmbeddedEnv::EmbeddedEnv(const std::string& resource_path)
    : resource_path_(resource_path)
{
}


void EmbeddedEnv::load_env() {
    std::string env_content = extract_env_content();
    parse_env(env_content);
}


std::string EmbeddedEnv::extract_env_content()
{
    GError* error = NULL;
    GBytes* env_bytes = g_resources_lookup_data(resource_path_.c_str(), G_RESOURCE_LOOKUP_FLAGS_NONE, &error);

    if (!env_bytes) {
        std::string error_message = "Failed to load embedded .env file from resource: " + resource_path_;
        if (error) {
            error_message += " - " + std::string(error->message);
            g_error_free(error);
        }
        throw std::runtime_error(error_message);
    }

    gsize size;
    const gchar* env_data = static_cast<const gchar*>(g_bytes_get_data(env_bytes, &size));
    std::string env_content(env_data, size);
    g_bytes_unref(env_bytes);

    return env_content;
}


void EmbeddedEnv::parse_env(const std::string& env_content) {
    std::istringstream stream(env_content);
    std::string line;

    while (std::getline(stream, line)) {
        if (line.empty() || line[0] == '#') {
            continue;
        }

        std::size_t equal_pos = line.find('=');
        if (equal_pos == std::string::npos) {
            throw std::runtime_error("Invalid .env line: " + line);
        }

        std::string key = line.substr(0, equal_pos);
        std::string value = line.substr(equal_pos + 1);

        key = trim(key);
        value = trim(value);

        // Set the environment variable
#if defined(_WIN32)
        _putenv_s(key.c_str(), value.c_str());  // Windows-specific
#else
        setenv(key.c_str(), value.c_str(), 1);  // POSIX-compliant
#endif
    }
}


std::string EmbeddedEnv::trim(const std::string& str) {
    const char* whitespace = " \t\n\r\f\v";
    std::size_t start = str.find_first_not_of(whitespace);
    std::size_t end = str.find_last_not_of(whitespace);

    if (start == std::string::npos || end == std::string::npos) {
        return "";
    }

    return str.substr(start, end - start + 1);
}