#ifndef DATABASEMANAGER_HPP
#define DATABASEMANAGER_HPP

#include "Types.hpp"
#include <string>
#include <map>
#include <vector>
#include <sqlite3.h>

class DatabaseManager {
public:
    DatabaseManager(std::string config_dir);
    ~DatabaseManager();

    bool is_file_already_categorized(const std::string &file_name);
    bool insert_or_update_file_with_categorization(const std::string& file_name,
                                                   const std::string& file_type,
                                                   const std::string& dir_path, 
                                                   const std::string& category, 
                                                   const std::string& subcategory);
    std::vector<std::string> get_dir_contents_from_db(const std::string &dir_path);

    std::vector<CategorizedFile> get_categorized_files(const std::string &directory_path);

    std::vector<std::string>
        get_categorization_from_db(const std::string& file_name, const FileType file_type);

private:
    std::map<std::string, std::string> cached_results;
    std::string get_cached_category(const std::string &file_name);
    void load_cache();
    bool file_exists_in_db(const std::string &file_name, const std::string &file_path);

    sqlite3* db;
    const std::string config_dir;
    const std::string db_file;
};

#endif
