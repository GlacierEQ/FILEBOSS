#include "MainApp.hpp"
#include "CategorizationSession.hpp"
#include "CryptoManager.hpp"
#include "ErrorMessages.hpp"
#include "FileScanner.hpp"
#include "LLMClient.hpp"
#include "Logger.hpp"
#include "MainAppEditActions.hpp"
#include "MainAppHelpActions.hpp"
#include "Updater.hpp"
#include "Utils.hpp"
#include "Types.hpp"

#include <chrono>
#include <filesystem>
#include <future>
#include <iostream>
#include <gtk/gtk.h>
#include <gtk/gtkfilechooser.h>
#include <gtk/gtkwidget.h>
#include <gtk/gtkentry.h>
#include <gtk/gtkdialog.h>
#include <gobject/gsignal.h>
#include <gtkmm/builder.h>
#include <gtkmm/dialog.h>
#include <gtkmm/treeview.h>
#include <gtkmm/liststore.h>
#include <glibmm/fileutils.h>
#include <string>
#include <thread>
#include <unordered_set>
#include <vector>

extern GResource *resources_get_resource();


MainApp::MainApp(int argc, char **argv)
    : builder(nullptr),
      settings(),
      db_manager(settings.get_config_dir()),
      categorization_dialog(nullptr),
      use_subcategories_checkbox(nullptr), 
      categorize_files_checkbox(nullptr), 
      categorize_directories_checkbox(nullptr),
      core_logger(Logger::get_logger("core_logger")),
      ui_logger(Logger::get_logger("ui_logger")),
      file_scan_options(FileScanOptions::None)
{
    stop_analysis = false;

    gtk_app = create_app();
    g_signal_connect(gtk_app, "activate", G_CALLBACK(on_activate_wrapper), this);
    g_application_run(G_APPLICATION(gtk_app), argc, argv);
    g_object_unref(gtk_app);
}


GtkApplication* MainApp::create_app()
{
    #if GLIB_CHECK_VERSION(2, 74, 0)
        return gtk_application_new("net.quicknode.AIFileSorter", G_APPLICATION_DEFAULT_FLAGS);
    #else
        return gtk_application_new("net.quicknode.AIFileSorter", G_APPLICATION_FLAGS_NONE);
    #endif
}


void MainApp::on_activate_wrapper(GtkApplication *gtk_app, gpointer user_data)
{
    MainApp *self = static_cast<MainApp*>(user_data);
    self->on_activate();
}


void MainApp::on_quit()
{
    save_settings();
    g_application_quit(G_APPLICATION(gtk_app));
}


void MainApp::load_settings() {
    if (!settings.load()) {
        core_logger->info("Failed to load settings, using defaults.");
    }
    sync_settings_to_ui();
}


void MainApp::save_settings() {
    sync_ui_to_settings();
    settings.save();
}


void MainApp::initialize_checkboxes() {
    use_subcategories_checkbox = GTK_CHECK_BUTTON(gtk_builder_get_object(builder, "use_subcategories_checkbox"));
    categorize_files_checkbox = GTK_CHECK_BUTTON(gtk_builder_get_object(builder, "categorize_files_checkbox"));
    categorize_directories_checkbox = GTK_CHECK_BUTTON(gtk_builder_get_object(builder, "categorize_directories_checkbox"));

    if (!use_subcategories_checkbox || !categorize_files_checkbox || !categorize_directories_checkbox) {
        g_critical("Failed to load one or more checkboxes.");
        return;
    }

    if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(categorize_files_checkbox))) {
        file_scan_options = file_scan_options | FileScanOptions::Files;
    }

    if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(categorize_directories_checkbox))) {
        file_scan_options = file_scan_options | FileScanOptions::Directories;
    }

    data_for_files = new CheckboxData{this, categorize_directories_checkbox};
    data_for_directories = new CheckboxData{this, categorize_files_checkbox};

    g_signal_connect(categorize_files_checkbox, "toggled", G_CALLBACK(MainApp::on_checkbox_toggled), data_for_files);
    g_signal_connect(categorize_directories_checkbox, "toggled", G_CALLBACK(MainApp::on_checkbox_toggled), data_for_directories);
}


void MainApp::sync_ui_to_settings() {
    const char* entry_text = gtk_entry_get_text(path_entry);
    settings.set_use_subcategories(gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(use_subcategories_checkbox)));
    settings.set_categorize_files(gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(categorize_files_checkbox)));
    settings.set_categorize_directories(gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(categorize_directories_checkbox)));
    settings.set_sort_folder(entry_text);
}


void MainApp::sync_settings_to_ui() {
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(use_subcategories_checkbox), settings.get_use_subcategories());
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(categorize_files_checkbox), settings.get_categorize_files());
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(categorize_directories_checkbox), settings.get_categorize_directories());

    const std::string& sort_folder = settings.get_sort_folder();

    gtk_entry_set_text(GTK_ENTRY(path_entry), sort_folder.c_str());

    if (g_file_test(sort_folder.c_str(), G_FILE_TEST_IS_DIR)) {
        gtk_file_chooser_set_current_folder(GTK_FILE_CHOOSER(file_chooser), sort_folder.c_str());
    } else {
        g_warning("Sort folder path is invalid: %s", sort_folder.c_str());
    }

    if (use_subcategories_checkbox) {
        gboolean is_checked = settings.get_use_subcategories();
        gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(use_subcategories_checkbox), is_checked);
    }
}


void MainApp::on_checkbox_toggled(GtkCheckButton* checkbox, gpointer user_data)
{
    CheckboxData* data = static_cast<CheckboxData*>(user_data);
    MainApp* app = data->app;
    GtkCheckButton* other_checkbox = data->other_checkbox;

    app->ensure_one_checkbox(checkbox, other_checkbox);

    FileScanOptions option = (checkbox == app->categorize_files_checkbox)
                             ? FileScanOptions::Files : FileScanOptions::Directories;

    app->update_file_scan_options(option, gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(checkbox)));
    app->update_checkbox_settings(checkbox);
}


void MainApp::ensure_one_checkbox(GtkCheckButton* checkbox, GtkCheckButton* other_checkbox)
{
    bool is_checkbox_active = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(checkbox));
    bool is_other_checkbox_active = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(other_checkbox));

    if (!is_checkbox_active && !is_other_checkbox_active) {
        gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(other_checkbox), TRUE);
    }
}


void MainApp::update_file_scan_options(FileScanOptions option, bool is_active)
{
    if (is_active) {
        file_scan_options = file_scan_options | option;
    } else {
        file_scan_options = file_scan_options & ~option;
    }
}


void MainApp::update_checkbox_settings(GtkCheckButton* checkbox)
{
    if (checkbox == categorize_files_checkbox) {
        settings.set_categorize_files(gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(checkbox)));
    } else {
        settings.set_categorize_directories(gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(checkbox)));
    }
}


std::unordered_set<std::string> MainApp::extract_file_names(
    const std::vector<CategorizedFile>& categorized_files)
{
    std::unordered_set<std::string> file_names;
    for (const auto& [file_path, file_name, file_type, category, subcategory] : categorized_files) {
        file_names.insert(file_name);
    }
    return file_names;
}


gboolean MainApp::update_ui_after_analysis()
{
    stop_analysis = false;
    gtk_button_set_label(analyze_button, "Analyze folder");

    if (new_files_to_sort.empty()) {
        show_error_dialog(ERR_NO_FILES_TO_CATEGORIZE);

        if (analyze_thread.joinable()) {
            analyze_thread.join();
        }

        return FALSE;
    }

    show_results_dialog(new_files_to_sort);

    if (analyze_thread.joinable()) {
        analyze_thread.join();
    }

    return FALSE;
}


void MainApp::show_error_dialog(const std::string &message) {
    GtkWidget *dialog = gtk_dialog_new();
    gtk_window_set_title(GTK_WINDOW(dialog), "Error");
    gtk_window_set_modal(GTK_WINDOW(dialog), TRUE);
    gtk_window_set_transient_for(GTK_WINDOW(dialog), GTK_WINDOW(this->main_window));

    GtkWidget *content_area = gtk_dialog_get_content_area(GTK_DIALOG(dialog));
    GtkWidget *label = gtk_label_new(message.c_str());
    gtk_widget_set_margin_top(label, 10);
    gtk_widget_set_margin_bottom(label, 10);
    gtk_widget_set_margin_start(label, 20);
    gtk_widget_set_margin_end(label, 20);
    gtk_box_pack_start(GTK_BOX(content_area), label, TRUE, TRUE, 0);

    GtkWidget *ok_button = gtk_button_new_with_label("OK");
    gtk_widget_set_hexpand(ok_button, TRUE);
    gtk_widget_set_halign(ok_button, GTK_ALIGN_CENTER);
    g_signal_connect(ok_button, "clicked", G_CALLBACK(+[](GtkWidget *widget, gpointer dialog) {
        gtk_widget_destroy(GTK_WIDGET(dialog));
    }), dialog);
    gtk_box_pack_start(GTK_BOX(content_area), ok_button, FALSE, FALSE, 0);

    gtk_widget_show_all(dialog);
}


void MainApp::perform_analysis()
{
    std::string directory_path = get_folder_path();
    if (directory_path.empty()) {
        g_idle_add([](gpointer user_data) -> gboolean {
            MainApp* app = static_cast<MainApp*>(user_data);
            app->show_error_dialog("No folder path provided.");
            return G_SOURCE_REMOVE;
        }, this);
        return;
    }

    g_idle_add([](gpointer user_data) -> gboolean {
        MainApp* app = static_cast<MainApp*>(user_data);
        app->progress_dialog->append_text("Analyzing contents of " + app->get_folder_path() + "\n");
        return G_SOURCE_REMOVE;
    }, this);

    if (stop_analysis) {
        return;
    }

    try {
        already_categorized_files = db_manager.get_categorized_files(directory_path);

        if (!already_categorized_files.empty()) {
            g_idle_add([](gpointer user_data) -> gboolean {
                MainApp* app = static_cast<MainApp*>(user_data);
                app->progress_dialog->append_text("\nAlready categorized files:\n");
                return G_SOURCE_REMOVE;
            }, this);
        }

        for (const auto& file_entry : already_categorized_files) {
            auto context = std::make_unique<AnalysisContext>(
                                                                this,
                                                                file_entry.file_name,
                                                                file_entry.type,
                                                                file_entry.category,
                                                                file_entry.subcategory
                                                            );

            g_idle_add([](gpointer user_data) -> gboolean {
                auto ctx = std::unique_ptr<AnalysisContext>(static_cast<AnalysisContext*>(user_data));
                ctx->app->progress_dialog->append_text(ctx->file_name + " [" + ctx->category + "/" + ctx->subcategory + "]\n");
                return G_SOURCE_REMOVE;
            }, context.release());
        }


        std::unordered_set<std::string> cached_file_names = extract_file_names(already_categorized_files);
        
        if (stop_analysis) {
            return;
        }

        files_to_categorize = find_files_to_categorize(directory_path, cached_file_names);

        if (!files_to_categorize.empty()) {
            g_idle_add([](gpointer user_data) -> gboolean {
                MainApp* app = static_cast<MainApp*>(user_data);
                app->progress_dialog->append_text("\nFiles to categorize:\n");
                return G_SOURCE_REMOVE;
            }, this);
        } else {
            g_idle_add([](gpointer user_data) -> gboolean {
                MainApp* app = static_cast<MainApp*>(user_data);
                app->progress_dialog->append_text("\nNo files to categorize\n");
                return G_SOURCE_REMOVE;
            }, this);
        }

        for (const auto& file_entry : files_to_categorize) {
            auto* context = new AnalysisContext(
                                                this,
                                                file_entry.file_name,
                                                file_entry.type,
                                                "",  // No category
                                                ""   // No subcategory
                                                );

            g_idle_add([](gpointer user_data) -> gboolean {
                auto* ctx = static_cast<AnalysisContext*>(user_data);
                ctx->app->progress_dialog->append_text(ctx->file_name + "\n");
                delete ctx;
                return G_SOURCE_REMOVE;
            }, context);
        }

        if (stop_analysis) {
            return;
        }

        g_idle_add([](gpointer user_data) -> gboolean {
            MainApp* app = static_cast<MainApp*>(user_data);
            app->progress_dialog->append_text("\n");
            return G_SOURCE_REMOVE;
        }, this);

        this->new_files_with_categories = categorize_files(files_to_categorize);

        this->already_categorized_files.insert(
            already_categorized_files.end(),
            new_files_with_categories.begin(),
            new_files_with_categories.end()
        );

        this->new_files_to_sort = compute_files_to_sort();

        g_idle_add([](gpointer user_data) -> gboolean {
            MainApp* app = static_cast<MainApp*>(user_data);

            if (app->progress_dialog) {
                app->progress_dialog->hide();
                delete app->progress_dialog;
                app->progress_dialog = nullptr;
            }

            return app->update_ui_after_analysis();
        }, this);
    } catch (const std::exception& ex) {
        show_error_dialog("Analysis Error: " + std::string(ex.what()));
        g_printerr("Exception during analysis: %s\n", ex.what());
    }
}


std::vector<FileEntry>
MainApp::get_actual_files(const std::string& directory_path)
{
    core_logger->info("Getting actual files from directory %s", directory_path.c_str());

    std::vector<FileEntry> actual_files =
        dirscanner.get_directory_entries(directory_path, FileScanOptions::Files | FileScanOptions::Directories);
    
    core_logger->info("Actual files found: %d\n", static_cast<int>(actual_files.size()));

    for (const auto& [full_file_path, file_name, file_type] : actual_files) {
        core_logger->info("File: %s, Path: %s\n", file_name.c_str(), full_file_path.c_str());
    }

    return actual_files;
}


void MainApp::on_analyze_button_clicked(GtkButton *button, gpointer main_app_instance)
{
    MainApp *app = static_cast<MainApp*>(main_app_instance);

    const char *folder_path = gtk_entry_get_text(app->path_entry);
    if (!Utils::is_valid_directory(folder_path)) {
        app->show_error_dialog(ERR_INVALID_PATH);
        return;
    }

    if (!Utils::is_network_available()) {
        app->show_error_dialog(ERR_NO_INTERNET_CONNECTION);
        return;
    }

    if (app->analyze_thread.joinable()) {
        app->stop_analysis = true;
        app->analyze_thread.join();
        gtk_button_set_label(button, "Analyze folder");
        return;
    }

    app->stop_analysis = false;
    gtk_button_set_label(button, "Stop Analyzing");

    g_idle_add([](gpointer user_data) -> gboolean {
        MainApp* app = static_cast<MainApp*>(user_data);
        gboolean show_subcategory_col = gtk_toggle_button_get_active(
            GTK_TOGGLE_BUTTON(app->use_subcategories_checkbox));
        app->progress_dialog = new CategorizationProgressDialog(
            GTK_WINDOW(app->main_window),
            app, show_subcategory_col);
        app->progress_dialog->show();
        return G_SOURCE_REMOVE;
    }, app);

    app->analyze_thread = std::thread([app]() {
        try {
            app->perform_analysis();
        } catch (const std::exception &ex) {
            app->core_logger->error("Exception during analysis: %s\n", ex.what());
        }
    });
}


std::vector<FileEntry>
MainApp::find_files_to_categorize(const std::string& directory_path,
                                  const std::unordered_set<std::string>& cached_files)
{
    std::vector<FileEntry> actual_files =
        dirscanner.get_directory_entries(directory_path, file_scan_options);
    std::vector<FileEntry> found_files;

    for (const auto &[full_file_path, file_name, file_type] : actual_files) {
        if (!cached_files.contains(file_name)) {
            found_files.push_back({full_file_path, file_name, file_type});
        }
    }

    return found_files;
}


std::vector<CategorizedFile> MainApp::compute_files_to_sort()
{
    std::vector<CategorizedFile> files_to_sort;
    
    // Get current files in the directory (full path and name)
    std::vector<FileEntry> actual_files = dirscanner.get_directory_entries(
                                              get_folder_path(), file_scan_options
                                              );
    
    for (const auto &[full_file_path, file_name, file_type] : actual_files) {
        // Search for each file in already_categorized_files to get its category data
        auto it = std::find_if(
            already_categorized_files.begin(), 
            already_categorized_files.end(),
            [&file_name, &file_type](const CategorizedFile& categorized_file) {
                return categorized_file.file_name == file_name && categorized_file.type == file_type;
            }
        );

        if (it != already_categorized_files.end()) {
            // Add files that are found in already_categorized_files with full metadata
            files_to_sort.push_back(*it);
        }
    }

    return files_to_sort;
}


std::string MainApp::get_folder_path()
{
    if (!GTK_IS_ENTRY(path_entry)) {
        g_print("Error: Path entry not found or invalid.\n");
        return "";
    }

    const char *folder_path = gtk_entry_get_text(path_entry);
    return std::string(folder_path);
}


std::tuple<std::string, std::string> split_category_subcategory(const std::string& input)
{
    std::string delimiter = " : ";
    size_t colon_pos = input.find(delimiter);
    if (colon_pos != std::string::npos) {
        std::string category = input.substr(0, colon_pos);
        std::string subcategory = input.substr(colon_pos + delimiter.length());
        return std::make_tuple(category, subcategory);
    } else {
        return std::make_tuple(input, "");
    }
}


std::vector<CategorizedFile> 
MainApp::categorize_files(const std::vector<FileEntry>& items)
{
    CategorizationSession categorization_session;
    LLMClient llm = categorization_session.create_llm_client();

    std::vector<CategorizedFile> categorized_items;

    for (const auto &[full_path, name, type] : items) {
        if (stop_analysis) {
            core_logger->info("Stopping categorization...\n");
            return categorized_items;
        }

        try {
            const std::string& dir_path = std::filesystem::path(full_path).parent_path().string();
            
            auto report_progress = [this](const std::string& message) {
                auto progress_data = std::make_unique<std::pair<MainApp*, std::string>>(this, message);

                g_idle_add([](gpointer user_data) -> gboolean {
                    auto progress_data = std::unique_ptr<std::pair<MainApp*, std::string>>(
                        static_cast<std::pair<MainApp*, std::string>*>(user_data)
                    );

                    if (progress_data->first->progress_dialog) {
                        progress_data->first->progress_dialog->append_text(progress_data->second + "\n");
                    }

                    return G_SOURCE_REMOVE;
                }, progress_data.release());
            };

            auto [category, subcategory] = categorize_file(llm, name, type, report_progress);

            categorized_items.emplace_back(CategorizedFile{
                                                dir_path,
                                                name,
                                                type,
                                                category,
                                                subcategory
                                            });

        } catch (const std::exception& ex) {
            std::string error_message = "Error categorizing file \"" + name + "\": " + ex.what();
            show_error_dialog(error_message);
            core_logger->error("%s\n", error_message.c_str());
            break;
        }
    }

    return categorized_items;
}


std::string MainApp::categorize_with_timeout(LLMClient& llm, const std::string& item_name,
                                             const FileType file_type, int timeout_seconds)
{
    std::promise<std::string> promise;
    std::future<std::string> future = promise.get_future();

    std::thread([&llm, promise = std::move(promise), item_name, file_type]() mutable {
        try {
            std::string result = llm.categorize_file(item_name, file_type);
            promise.set_value(result);
        } catch (const std::exception& e) {
            promise.set_exception(std::current_exception());
        }
    }).detach();

    // Wait for result
    if (future.wait_for(std::chrono::seconds(timeout_seconds)) == std::future_status::ready) {
        return future.get();
    } else {
        throw std::runtime_error("Network timeout: LLM response took too long.");
    }
}


std::tuple<std::string, std::string>
MainApp::categorize_file(LLMClient& llm, const std::string& item_name,
                         const FileType file_type,
                         const std::function<void(const std::string&)>& report_progress)
{
    // Check the local database with the item name and type
    auto categorization = db_manager.get_categorization_from_db(item_name, file_type);
    if (categorization.size() >= 2) {
        std::string category = categorization[0];
        std::string subcategory = categorization[1];
        core_logger->info("Found in local DB: %s - Category: %s, Subcategory: %s\n", item_name.c_str(), category.c_str(), subcategory.c_str());
        std::string message = 
            "\nFound in local DB: " + item_name + " [" + category + "/" + subcategory + "]";
        report_progress(message);
        return std::make_tuple(category, subcategory);
    }

    const char* env_pc = std::getenv("ENV_PC");
    const char* env_rr = std::getenv("ENV_RR");

    std::string key;
    try {
        CryptoManager crypto(env_pc, env_rr);
        key = crypto.reconstruct();
    } catch (const std::exception& ex) {
        std::string message = "CryptoManager error for \"" + item_name + "\": " + ex.what();
        report_progress(message);
        g_printerr("%s\n", message.c_str());
        return std::make_tuple("", "");
    }

    try {
        std::string category_subcategory;
        try {
            category_subcategory = categorize_with_timeout(llm, item_name, file_type, 10);
        } catch (const std::exception& ex) {
            std::string message = "LLM Timeout/Error: " + std::string(ex.what());
            report_progress(message);
            g_printerr("%s\n", message.c_str());
            return std::make_tuple("", "");
        }

        auto [category, subcategory] = split_category_subcategory(category_subcategory);

        std::ostringstream message;
        message << "Suggested by AI: " << item_name << " [" << category << "/" << subcategory << "]";
        report_progress(message.str());

        return std::make_tuple(category, subcategory);
    } catch (const std::exception& ex) {
        std::ostringstream message;
        message << "LLM Error \"" << ex.what();
        report_progress(message.str());
        g_printerr("%s\n", message.str().c_str());
        throw;
    }
}


void MainApp::show_results_dialog(const std::vector<CategorizedFile>& results)
{
    try {
        delete categorization_dialog;
        gboolean show_subcategory_col = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(use_subcategories_checkbox));
        categorization_dialog = new CategorizationDialog(&db_manager, show_subcategory_col);
        this->categorization_dialog->show_results(results);
    } catch (const std::runtime_error &ex) {
        ui_logger->error("Error: %s\n", ex.what());;
    }
}


void MainApp::on_file_chooser_response(GtkDialog *dialog, gint response, gpointer user_data) {
    MainApp *app = static_cast<MainApp *>(user_data);

    if (response == GTK_RESPONSE_ACCEPT) {
        GtkFileChooser *chooser = GTK_FILE_CHOOSER(dialog);
        char *folder_path = gtk_file_chooser_get_filename(chooser);
        gtk_entry_set_text(GTK_ENTRY(app->path_entry), folder_path);
        gtk_file_chooser_set_current_folder(GTK_FILE_CHOOSER(app->file_chooser), folder_path);
        g_free(folder_path);
    }

    gtk_widget_destroy(GTK_WIDGET(dialog));
}


void MainApp::on_browse_button_clicked(GtkButton *button, gpointer user_data) {
    MainApp *app = static_cast<MainApp *>(user_data);

    GtkWidget *dialog;
    GtkWidget *window = gtk_widget_get_toplevel(GTK_WIDGET(button));

    dialog = gtk_file_chooser_dialog_new("Select Directory",
                                         GTK_WINDOW(window),
                                         GTK_FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                         "_Cancel", GTK_RESPONSE_CANCEL,
                                         "_Open", GTK_RESPONSE_ACCEPT,
                                         NULL);

    g_signal_connect(dialog, "response", G_CALLBACK(MainApp::on_file_chooser_response), app);

    gtk_widget_show(dialog);
}


void MainApp::setup_menu_item_file_explorer()
{
    GtkWidget *check_menu_item = GTK_WIDGET(gtk_builder_get_object(builder, "view-file-explorer"));
    GtkWidget *icon_image = gtk_image_new_from_icon_name("document-open", GTK_ICON_SIZE_MENU);
    GtkWidget *hbox = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);

    gtk_box_pack_start(GTK_BOX(hbox), icon_image, FALSE, FALSE, 0);

    GtkWidget *label = gtk_label_new("File Explorer");
    gtk_box_pack_start(GTK_BOX(hbox), label, FALSE, FALSE, 0);

    GtkWidget *existing_child = gtk_bin_get_child(GTK_BIN(check_menu_item));
    gtk_container_remove(GTK_CONTAINER(check_menu_item), existing_child);

    gtk_container_add(GTK_CONTAINER(check_menu_item), hbox);

    gtk_widget_show_all(check_menu_item);
}


void MainApp::on_directory_selected(GtkFileChooser *file_chooser, gpointer user_data)
{
    MainApp *app = static_cast<MainApp *>(user_data);
    char *selected_dir = gtk_file_chooser_get_filename(file_chooser);

    if (selected_dir != nullptr) {
        gtk_entry_set_text(app->path_entry, selected_dir);
        g_free(selected_dir);
    }
}


void MainApp::on_toggle_file_explorer(GtkCheckMenuItem *menu_item, GtkWidget *directory_browser)
{
    gboolean active = gtk_check_menu_item_get_active(menu_item);
    GtkWindow *main_window = GTK_WINDOW(gtk_widget_get_toplevel(GTK_WIDGET(directory_browser)));

    int width, height;
    gtk_window_get_size(main_window, &width, &height);

    const int height_adjustment = gtk_widget_get_allocated_height(directory_browser);

    if (active) {
        gtk_widget_show(directory_browser);
        gtk_window_resize(main_window, width, height + height_adjustment);
    } else {
        gtk_widget_hide(directory_browser);
        gtk_window_resize(main_window, width, height - height_adjustment);
    }
}


void MainApp::on_path_entry_activate(GtkEntry *path_entry, gpointer user_data)
{
    MainApp *app = static_cast<MainApp *>(user_data);
    const char *folder_path = gtk_entry_get_text(app->path_entry);

    if (g_file_test(folder_path, G_FILE_TEST_IS_DIR)) {
        gtk_file_chooser_set_current_folder(GTK_FILE_CHOOSER(app->file_chooser), folder_path);
    } else {
        app->show_error_dialog(ERR_INVALID_PATH);
    }
}


void MainApp::on_activate()
{
    try {
        initialize_builder();
        setup_main_window();
        initialize_ui_components();
        start_updater();
    } catch (const std::exception &e) {
        ui_logger->critical("Exception in MainApp::on_activate: %s", e.what());
    }
}


void MainApp::initialize_builder() {
    builder = gtk_builder_new();
    if (!builder) {
        ui_logger->critical("Failed to initialize GtkBuilder.");
        throw std::runtime_error("GtkBuilder initialization failed.");
    }
    GError *error = NULL;
    if (!gtk_builder_add_from_resource(builder, "/net/quicknode/AIFileSorter/ui/main_window.glade", &error)) {
        ui_logger->critical("Failed to load resource: %s", error->message);
        g_error_free(error);
        g_object_unref(builder);
        throw std::runtime_error("Resource loading failed.");
    }
}


void MainApp::setup_main_window() {
    main_window = GTK_WIDGET(gtk_builder_get_object(builder, "main_window"));
    if (!main_window) {
        ui_logger->critical("Failed to load 'main_window'.");
        throw std::runtime_error("Failed to load 'main_window'.");
    }

    gtk_window_set_application(GTK_WINDOW(main_window), GTK_APPLICATION(gtk_app));
    set_app_icon();
    gtk_widget_show_all(main_window);
}


void MainApp::initialize_ui_components() {
    initialize_checkboxes();
    gboolean show_subcategory_col = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(use_subcategories_checkbox));
    categorization_dialog = new CategorizationDialog(&db_manager, show_subcategory_col);
    connect_ui_signals();
    setup_menu_item_file_explorer();
    load_settings();
}


void MainApp::start_updater() {
    Updater* updater = new Updater(settings);
    updater->begin();
}


void MainApp::set_app_icon()
{
    GError *error = NULL;
    GdkPixbuf *pixbuf_icon = gdk_pixbuf_new_from_resource("/net/quicknode/AIFileSorter/images/app_icon_128.png", &error);
    
    if (!pixbuf_icon) {
        ui_logger->critical("Failed to load the app icon resource: %s", error->message);
        g_clear_error(&error);
    } else {
        gtk_window_set_icon(GTK_WINDOW(main_window), pixbuf_icon);

        // Debugging: Check the reference count before unref
        g_object_ref(pixbuf_icon);  // Increase ref count to check
        gsize ref_count = G_OBJECT(pixbuf_icon)->ref_count;
        ui_logger->debug("Pixbuf ref count before unref: %zu", ref_count);

        g_object_unref(pixbuf_icon);
    }
}


void MainApp::on_about_activate() {
    MainAppHelpActions::show_about(GTK_WINDOW(main_window));
}


void MainApp::on_donate_activate() {
    const std::string donation_url = "https://filesorter.app/donate";

    #ifdef __linux__
        const std::string command = "xdg-open " + donation_url;
    #elif _WIN32
        const std::string command = "start " + donation_url;
    #elif __APPLE__
        const std::string command = "open " + donation_url;
    #else
        g_printerr("Unsupported platform for opening URLs\n");
        return;
    #endif

    int result = std::system(command.c_str());
    if (result != 0) {
        g_printerr("Failed to open the donation URL: %s\n", donation_url.c_str());
    }
}


void MainApp::connect_ui_signals() {
    // File > Quit
    GtkWidget* file_quit_menu_item = GTK_WIDGET(gtk_builder_get_object(builder, "file-quit"));
    g_signal_connect(file_quit_menu_item, "activate", G_CALLBACK(+[](GtkWidget*, gpointer user_data) {
        static_cast<MainApp*>(user_data)->on_quit();
    }), this);

    // Window close (delete-event)
    g_signal_connect(main_window, "delete-event", G_CALLBACK(+[](GtkWidget*, GdkEvent*, gpointer user_data) -> gboolean {
        static_cast<MainApp*>(user_data)->on_quit();
        return FALSE;
    }), this);

    // File chooser and path entry
    file_chooser = GTK_FILE_CHOOSER_WIDGET(gtk_builder_get_object(builder, "directory_browser"));
    if (file_chooser) {
        g_signal_connect(file_chooser, "selection-changed", G_CALLBACK(&MainApp::on_directory_selected), this);
    } else {
        g_critical("Failed to load 'directory_browser'.");
    }

    path_entry = GTK_ENTRY(gtk_builder_get_object(builder, "path_entry"));
    if (path_entry) {
        g_signal_connect(path_entry, "activate", G_CALLBACK(MainApp::on_path_entry_activate), this);
    } else {
        g_critical("Failed to load 'path_entry'.");
    }

    // View > File Explorer
    GtkCheckMenuItem *view_file_explorer = GTK_CHECK_MENU_ITEM(gtk_builder_get_object(builder, "view-file-explorer"));
    GtkWidget *directory_browser = GTK_WIDGET(gtk_builder_get_object(builder, "directory_browser"));
    if (view_file_explorer && directory_browser) {
        g_signal_connect(view_file_explorer, "toggled", G_CALLBACK(on_toggle_file_explorer), directory_browser);
    } else {
        g_critical("Failed to load 'view-file-explorer' or 'directory_browser'.");
    }

    // Browse button
    GtkWidget *browse_button = GTK_WIDGET(gtk_builder_get_object(builder, "browse_button"));
    if (browse_button && path_entry) {
        g_signal_connect(browse_button, "clicked", G_CALLBACK(MainApp::on_browse_button_clicked), this);
    } else {
        g_critical("Failed to load 'browse_button'.");
    }

    // Analyze button
    analyze_button = GTK_BUTTON(gtk_builder_get_object(builder, "analyze_button"));
    if (analyze_button) {
        g_signal_connect(analyze_button, "clicked", G_CALLBACK(on_analyze_button_clicked), this);
    } else {
        g_critical("Failed to load 'analyze_button'.");
    }

    // Edit > Paste, Copy, Cut, Delete
    GtkWidget *edit_paste_menu_item = GTK_WIDGET(gtk_builder_get_object(builder, "edit-paste"));
    GtkWidget *edit_copy_menu_item = GTK_WIDGET(gtk_builder_get_object(builder, "edit-copy"));
    GtkWidget *edit_cut_menu_item = GTK_WIDGET(gtk_builder_get_object(builder, "edit-cut"));
    GtkWidget *edit_delete_menu_item = GTK_WIDGET(gtk_builder_get_object(builder, "edit-delete"));

    g_signal_connect(edit_paste_menu_item, "activate", G_CALLBACK(+[](GtkWidget*, gpointer user_data) {
        MainAppEditActions::on_paste(GTK_ENTRY(user_data));
    }), path_entry);

    g_signal_connect(edit_copy_menu_item, "activate", G_CALLBACK(+[](GtkWidget*, gpointer user_data) {
        MainAppEditActions::on_copy(GTK_ENTRY(user_data));
    }), path_entry);

    g_signal_connect(edit_cut_menu_item, "activate", G_CALLBACK(+[](GtkWidget*, gpointer user_data) {
        MainAppEditActions::on_cut(GTK_ENTRY(user_data));
    }), path_entry);

    g_signal_connect(edit_delete_menu_item, "activate", G_CALLBACK(+[](GtkWidget*, gpointer user_data) {
        MainAppEditActions::on_delete(GTK_ENTRY(user_data));
    }), path_entry);

    // Help > About
    GtkWidget* help_about_menu_item = GTK_WIDGET(gtk_builder_get_object(builder, "help-about"));
    if (!help_about_menu_item) {
        g_error("Failed to get 'help-about' menu item from UI file.");
    }
    g_signal_connect(help_about_menu_item, "activate", G_CALLBACK(+[](GtkWidget*, gpointer user_data) {
        MainApp* self = static_cast<MainApp*>(user_data);
        self->on_about_activate();
    }), this);

    // Help > Donate
    GtkWidget* help_donate_menu_item = GTK_WIDGET(gtk_builder_get_object(builder, "help-donate"));
    if (!help_donate_menu_item) {
        g_error("Failed to get 'help-donate' menu item from UI file.");
    }
    g_signal_connect(help_donate_menu_item, "activate", G_CALLBACK(+[](GtkWidget*, gpointer user_data) {
        MainApp* self = static_cast<MainApp*>(user_data);
        self->on_donate_activate();
    }), this);
}


void MainApp::run()
{
    // Nothing needed here for now, the app runs with gtk_application_run
}


void MainApp::shutdown() {
    if (analyze_thread.joinable()) {
        stop_analysis = true;
        analyze_thread.join();
    }

    g_signal_handlers_disconnect_by_data(categorize_files_checkbox, this);
    g_signal_handlers_disconnect_by_data(categorize_directories_checkbox, this);

    delete categorization_dialog;
    delete data_for_files;
    delete data_for_directories;

    if (categorize_files_checkbox) {
        g_object_unref(categorize_files_checkbox);
        categorize_files_checkbox = nullptr;
    }
    
    if (categorize_directories_checkbox) {
        g_object_unref(categorize_directories_checkbox);
        categorize_directories_checkbox = nullptr;
    }
}


MainApp::~MainApp()
{
    // FcFini();
}