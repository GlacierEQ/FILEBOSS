#include "IniConfig.hpp"
#include <iostream>


bool IniConfig::load(const std::string &filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Failed to open config file: " << filename << std::endl;
        return false;
    }

    std::string line, section;
    while (std::getline(file, line)) {
        // Remove whitespace
        line.erase(0, line.find_first_not_of(" \t"));
        line.erase(line.find_last_not_of(" \t") + 1);

        if (line.empty() || line[0] == ';' || line[0] == '#') continue;

        // New section
        if (line.front() == '[' && line.back() == ']') {
            section = line.substr(1, line.size() - 2);
        }
        // Key-value pair
        else {
            std::istringstream is_line(line);
            std::string key, value;
            if (std::getline(is_line, key, '=') && std::getline(is_line, value)) {
                // Remove whitespace
                key.erase(key.find_last_not_of(" \t") + 1);
                value.erase(0, value.find_first_not_of(" \t"));
                data[section][key] = value;
            }
        }
    }
    return true;
}


std::string IniConfig::getValue(const std::string &section, const std::string &key, const std::string &default_value) const {
    auto sec_it = data.find(section);
    if (sec_it != data.end()) {
        auto key_it = sec_it->second.find(key);
        if (key_it != sec_it->second.end()) {
            return key_it->second;
        }
    }
    return default_value;
}


void IniConfig::setValue(const std::string &section, const std::string &key, const std::string &value) {
    data[section][key] = value;
}


bool IniConfig::save(const std::string &filename) const
{
    std::ofstream file(filename);
    
    if (!file.is_open()) {
        std::cerr << "Failed to open config file: " << filename << std::endl;
        return false;
    }

    for (const auto &section : data) {
        file << "[" << section.first << "]\n";
        for (const auto &pair : section.second) {
            file << pair.first << " = " << pair.second << "\n";
        }
        file << "\n";
    }

    return true;
}