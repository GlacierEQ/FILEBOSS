#include "Settings.hpp"
#include <filesystem>
#include <iostream>
#include <glib.h>
#ifdef _WIN32
    #include <shlobj.h>
    #include <windows.h>
#endif


Settings::Settings()
    : use_subcategories(true),
      categorize_files(true),
      categorize_directories(false),
      default_sort_folder(""),
      sort_folder("")
{
    std::string AppName = "AIFileSorter";
    config_path = define_config_path();

    config_dir = std::filesystem::path(config_path).parent_path();

    try {
        if (!std::filesystem::exists(config_dir)) {
            std::filesystem::create_directories(config_dir);
        }
    } catch (const std::filesystem::filesystem_error &e) {
        std::cerr << "Error creating configuration directory: " << e.what() << std::endl;
    }
    this->default_sort_folder = g_get_user_special_dir(G_USER_DIRECTORY_DOWNLOAD);
    if (!this->default_sort_folder) {
        this->default_sort_folder = g_get_home_dir();
    }
    this->sort_folder = this->default_sort_folder;
}

std::string Settings::define_config_path()
{
    std::string AppName = "AIFileSorter";
#ifdef _WIN32
    char appDataPath[MAX_PATH];
    if (SUCCEEDED(SHGetFolderPath(NULL, CSIDL_APPDATA, NULL, 0, appDataPath))) {
        return std::string(appDataPath) + "\\" + AppName + "\\config.ini";
    }
#elif defined(__APPLE__)
    return std::string(getenv("HOME")) + "/Library/Application Support/" + AppName + "/config.ini";
#else
    return std::string(getenv("HOME")) + "/.config/" + AppName + "/config.ini";
#endif
    return "config.ini";
}

std::string Settings::get_config_dir()
{
    return config_dir.string();
}


bool Settings::load() {
    if (!config.load(config_path)) {
        sort_folder = default_sort_folder ? default_sort_folder : "/";
        return false;
    }

    use_subcategories = config.getValue("Settings", "UseSubcategories", "false") == "true";
    categorize_files = config.getValue("Settings", "CategorizeFiles", "true") == "true";
    categorize_directories = config.getValue("Settings", "CategorizeDirectories", "false") == "true";
    sort_folder = config.getValue("Settings", "SortFolder", default_sort_folder ? default_sort_folder : "/");
    skipped_version = config.getValue("Settings", "SkippedVersion", "0.0.0");

    return true;
}


bool Settings::save() {
    config.setValue("Settings", "UseSubcategories", use_subcategories ? "true" : "false");
    config.setValue("Settings", "CategorizeFiles", categorize_files ? "true" : "false");
    config.setValue("Settings", "CategorizeDirectories", categorize_directories ? "true" : "false");
    config.setValue("Settings", "SortFolder", this->sort_folder);

    if (!skipped_version.empty()) {
        config.setValue("Settings", "SkippedVersion", skipped_version);
    }

    return config.save(config_path);
}


bool Settings::get_use_subcategories() const
{
    return use_subcategories;
}


void Settings::set_use_subcategories(bool value)
{
    use_subcategories = value;
}


bool Settings::get_categorize_files() const
{
    return categorize_files;
}


void Settings::set_categorize_files(bool value)
{
    categorize_files = value;
}


bool Settings::get_categorize_directories() const
{
    return categorize_directories;
}


void Settings::set_categorize_directories(bool value)
{
    categorize_directories = value;
}


std::string Settings::get_sort_folder() const
{
    return sort_folder;
}


void Settings::set_sort_folder(const std::string &path)
{
    this->sort_folder = path;
}


void Settings::set_skipped_version(const std::string &version) {
    skipped_version = version;
}


std::string Settings::get_skipped_version()
{
    return skipped_version;
}