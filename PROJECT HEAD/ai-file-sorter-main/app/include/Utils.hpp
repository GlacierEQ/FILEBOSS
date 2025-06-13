#ifndef UTILS_HPP
#define UTILS_HPP

#include <string>
#include <vector>


class Utils {
public:
    Utils();
    ~Utils();
    static bool is_network_available();
    static std::string get_executable_path();
    static bool is_valid_directory(const char *path);
    static std::vector<unsigned char> hex_to_vector(const std::string &hex);
    static const char* to_cstr(const std::u8string& u8str);
    static void ensure_directory_exists(const std::string &dir);
};

#endif