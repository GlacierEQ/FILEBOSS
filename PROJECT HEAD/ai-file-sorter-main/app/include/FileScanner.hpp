#ifndef FILE_SCANNER_HPP
#define FILE_SCANNER_HPP

#include <filesystem>
#include <string>
#include <vector>
#include "Types.hpp"

namespace fs = std::filesystem;

class FileScanner {
public:
    FileScanner() = default;
    std::vector<FileEntry>
        get_directory_entries(const std::string &directory_path,
                              FileScanOptions options);

private:
    bool is_file_hidden(const fs::path &path);
};

#endif