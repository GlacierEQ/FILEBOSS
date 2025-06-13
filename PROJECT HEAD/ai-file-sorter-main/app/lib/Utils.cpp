#include "Utils.hpp"
#include <filesystem>
#include <stdlib.h>
#include <string>
#include <glibmm/fileutils.h>
#ifdef _WIN32
    #include <windows.h>
#elif __linux__
    #include <unistd.h>
    #include <limits.h>
#elif __APPLE__
    #include <mach-o/dyld.h>
    #include <limits.h>
#endif
#include <iostream>


bool Utils::is_network_available()
{
#ifdef _WIN32
    int result = system("ping -n 1 google.com > NUL 2>&1");
#else
    int result = system("ping -c 1 google.com > /dev/null 2>&1");
#endif
    return result == 0;
}


std::string Utils::get_executable_path()
{
#ifdef _WIN32
    char result[MAX_PATH];
    GetModuleFileName(NULL, result, MAX_PATH);
    return std::string(result);
#elif __linux__
    char result[PATH_MAX];
    ssize_t count = readlink("/proc/self/exe", result, PATH_MAX);
    return (count != -1) ? std::string(result, count) : "";
#elif __APPLE__
    char result[PATH_MAX];
    uint32_t size = sizeof(result);
    if (_NSGetExecutablePath(result, &size) == 0) {
        return std::string(result);
    } else {
        throw std::runtime_error("Path buffer too small");
    }
#else
    throw std::runtime_error("Unsupported platform");
#endif
}


bool Utils::is_valid_directory(const char *path)
{
    return g_file_test(path, G_FILE_TEST_IS_DIR);
}


std::vector<unsigned char> Utils::hex_to_vector(const std::string& hex) {
    std::vector<unsigned char> data;
    for (size_t i = 0; i < hex.length(); i += 2) {
        unsigned char byte = static_cast<unsigned char>(std::stoi(hex.substr(i, 2), nullptr, 16));
        data.push_back(byte);
    }
    return data;
}


const char* Utils::to_cstr(const std::u8string& u8str) {
    return reinterpret_cast<const char*>(u8str.c_str());
}


void Utils::ensure_directory_exists(const std::string &dir)
{
    try {
        if (!std::filesystem::exists(dir)) {
            std::filesystem::create_directories(dir);
        }
    } catch (const std::exception &e) {
        std::cerr << "Error creating log directory: " << e.what() << std::endl;
        throw;
    }
}