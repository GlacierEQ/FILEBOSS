#include "MovableCategorizedFile.hpp"
#include "Utils.hpp"
#include <filesystem>
#include <gtk/gtk.h>


MovableCategorizedFile::MovableCategorizedFile(
    const std::string& dir_path, const std::string& cat, const std::string& subcat,
    const std::string& file_name, const std::string& file_type)
    : file_name(file_name),
      file_type(file_type),
      dir_path(dir_path),
      category(cat),
      subcategory(subcat)
{
    if (dir_path.empty() || category.empty() || subcategory.empty() || file_name.empty()) {
        g_print("Error: One or more path components are empty.\n");
        throw std::runtime_error("Invalid path component in CategorizedFile constructor.");
    }

    category_path = std::filesystem::path(dir_path) / category;
    subcategory_path = category_path / subcategory;
    destination_path = subcategory_path / file_name;
}


void MovableCategorizedFile::create_cat_dirs(bool use_subcategory)
{
    try {
        if (!std::filesystem::exists(category_path)) {
            std::filesystem::create_directory(category_path);
        }
        if (use_subcategory && !std::filesystem::exists(subcategory_path)) {
            std::filesystem::create_directory(subcategory_path);
        }
    } catch (const std::filesystem::filesystem_error& e) {
        g_print("Error creating directories: %s\n", e.what());
        throw;
    }
}


bool MovableCategorizedFile::move_file(bool use_subcategory)
{
    std::filesystem::path categorized_path;
    if (use_subcategory) {
        categorized_path = std::filesystem::path(dir_path) / category / subcategory;
    } else {
        categorized_path = std::filesystem::path(dir_path) / category;
    }
    std::filesystem::path destination_path = categorized_path / file_name;
    std::filesystem::path source_path = std::filesystem::path(dir_path) / file_name;

    if (!std::filesystem::exists(source_path)) {
        g_print("Error: Source file does not exist: %s\n", Utils::to_cstr(source_path.u8string()));
        return false;
    }

    if (!std::filesystem::exists(destination_path)) {
        try {
            std::filesystem::rename(source_path, destination_path);
            g_print("File %s moved to %s\n", Utils::to_cstr(source_path.u8string()),
                                             Utils::to_cstr(destination_path.u8string()));
            return true;
        } catch (const std::filesystem::filesystem_error& e) {
            g_print("Error moving file: %s\n", e.what());
            return false;
        }
    } else {
        g_print("File %s already exists in %s\n", Utils::to_cstr(source_path.u8string()),
                                                  Utils::to_cstr(destination_path.u8string()));
        return false;
    }
}


std::string MovableCategorizedFile::get_subcategory_path() const
{
    return subcategory_path.string();
}


std::string MovableCategorizedFile::get_category_path() const
{
    return category_path.string();
}


std::string MovableCategorizedFile::get_destination_path() const
{
    return destination_path.string();
}


std::string MovableCategorizedFile::get_file_name() const
{
    return file_name;
}

std::string MovableCategorizedFile::get_dir_path() const
{
    return dir_path;
}

std::string MovableCategorizedFile::get_category() const
{
    return category;
}

std::string MovableCategorizedFile::get_subcategory() const
{
    return subcategory;
}

void MovableCategorizedFile::set_category(std::string& category)
{
    this->category = category;
}

void MovableCategorizedFile::set_subcategory(std::string& subcategory)
{
    this->subcategory = subcategory;
}

MovableCategorizedFile::~MovableCategorizedFile() {}