#include "FileScanner.hpp"
#include <iostream>
#include <filesystem>
#include <gtk/gtk.h>

#ifdef _WIN32
#include <windows.h>
#endif

namespace fs = std::filesystem;

std::vector<FileEntry>
FileScanner::get_directory_entries(const std::string &directory_path,
                                   FileScanOptions options)
{
    std::vector<FileEntry> file_paths_and_names;
    for (const auto &entry : fs::directory_iterator(directory_path)) {
        std::string full_path = entry.path().string();
        std::string file_name = entry.path().filename().string();
        FileType file_type;

        bool is_hidden = is_file_hidden(full_path);

        if (has_flag(options, FileScanOptions::Files) && fs::is_regular_file(entry)) {
            if (has_flag(options, FileScanOptions::HiddenFiles) || !is_hidden) {
                file_type = FileType::File;
            }
        } else if (has_flag(options, FileScanOptions::Directories) && fs::is_directory(entry)) {
            if (has_flag(options, FileScanOptions::HiddenFiles) || !is_hidden) {
                file_type = FileType::Directory;
            }
        }
        file_paths_and_names.push_back({full_path, file_name, file_type});
    }

    return file_paths_and_names;
}


bool FileScanner::is_file_hidden(const fs::path &path) {
    #ifdef _WIN32
    DWORD attrs = GetFileAttributesW(path.c_str());
    return (attrs != INVALID_FILE_ATTRIBUTES) && (attrs & FILE_ATTRIBUTE_HIDDEN);
    #endif
    return path.string().starts_with(".");
}