#ifndef MAINAPP_HPP
#define MAINAPP_HPP

#include "CategorizationDialog.hpp"
#include "CategorizationProgressDialog.hpp"
#include "DatabaseManager.hpp"
#include "FileScanner.hpp"
#include "LLMClient.hpp"
#include "Settings.hpp"

#include <gtk/gtk.h>
#include <gtkmm/builder.h>
#include <gtkmm/dialog.h>
#include <gtkmm/treeview.h>
#include <gtkmm/liststore.h>
#include <memory>
#include <spdlog/logger.h>
#include <string>
#include <thread>
#include <unordered_set>
#include <vector>

struct CheckboxData {
        MainApp* app;
        GtkCheckButton* other_checkbox;
    };


class MainApp {
public:
    GtkButton *analyze_button;
    GtkTreeView *treeview;
    std::vector<CategorizedFile> already_categorized_files;
    std::vector<CategorizedFile> new_files_with_categories;
    std::vector<FileEntry> files_to_categorize;
    std::vector<CategorizedFile> new_files_to_sort;
    
    CategorizationProgressDialog* progress_dialog;
    
    MainApp(int argc, char **argv);
    ~MainApp();
    void run();
    void shutdown();
    void show_results_dialog(const std::vector<CategorizedFile> &categorized_files);
    void show_error_dialog(const std::string &message);

    std::thread analyze_thread;
    bool stop_analysis;

    struct AnalysisContext {
        MainApp* app;
        std::string file_name;
        FileType file_type;
        std::string category;
        std::string subcategory;

        AnalysisContext(MainApp* app_instance, const std::string& name, const FileType& type,
                        const std::string& cat, const std::string& subcat)
            : app(app_instance), file_name(name), file_type(type), category(cat), subcategory(subcat) {}
    };

private:
    GtkApplication *gtk_app;
    GtkBuilder* builder;
    GtkWidget* main_window;
    Settings settings;
    DatabaseManager db_manager;
    CategorizationDialog* categorization_dialog;
    FileScanner dirscanner;
    GtkEntry* path_entry;
    GtkFileChooserWidget *file_chooser;
    GtkCheckButton *use_subcategories_checkbox;
    GtkCheckButton *categorize_files_checkbox;
    GtkCheckButton *categorize_directories_checkbox;
    std::shared_ptr<spdlog::logger> core_logger;
    std::shared_ptr<spdlog::logger> ui_logger;
    FileScanOptions file_scan_options;
    CheckboxData* data_for_files = nullptr;
    CheckboxData* data_for_directories = nullptr;

    GtkApplication *create_app();
    void initialize_checkboxes();
    static void on_file_chooser_response(GtkDialog *dialog, gint response, gpointer user_data);
    static void on_browse_button_clicked(GtkButton *button, gpointer user_data);
    static void on_checkbox_toggled(GtkCheckButton *checkbox, gpointer user_data);
    void ensure_one_checkbox(GtkCheckButton *checkbox, GtkCheckButton *other_checkbox);
    void update_file_scan_options(FileScanOptions option, bool is_active);
    void update_checkbox_settings(GtkCheckButton *checkbox);
    std::unordered_set<std::string> extract_file_names(const std::vector<CategorizedFile> &categorized_files);
    void on_activate();
    void initialize_builder();
    void setup_main_window();
    void initialize_ui_components();
    void start_updater();
    void on_about_activate();
    void on_donate_activate();
    void set_app_icon();
    void connect_ui_signals();
    static void on_activate_wrapper(GtkApplication *gtk_app, gpointer user_data);
    std::string get_folder_path();
    std::vector<CategorizedFile>
        categorize_files(const std::vector<FileEntry>& files);
    std::string categorize_with_timeout(LLMClient &llm, const std::string &item_name,
                                        const FileType file_type, int timeout_seconds);
    std::tuple<std::string, std::string> categorize_file(LLMClient &llm,
                                                         const std::string &item_name,
                                                         const FileType file_type,
                                                         const std::function<void(const std::string&)>& report_progress);
    std::vector<FileEntry> find_files_to_categorize(
        const std::string& directory_path, const std::unordered_set<std::string>& cached_files);
    static void on_analyze_button_clicked(GtkButton *button, gpointer user_data);
    void perform_analysis();
    void setup_menu_item_file_explorer();
    static void on_directory_selected(GtkFileChooser *file_chooser, gpointer user_data);
    static void on_toggle_file_explorer(GtkCheckMenuItem *menu_item, GtkWidget *directory_browser);
    static void on_path_entry_activate(GtkEntry *path_entry, gpointer user_data);
    std::vector<FileEntry> get_actual_files(const std::string &directory_path);
    std::vector<CategorizedFile> compute_files_to_sort();
    gboolean update_ui_after_analysis();
    void sync_ui_to_settings();
    void sync_settings_to_ui();
    void load_settings();
    void save_settings();
    void on_quit();
};

#endif