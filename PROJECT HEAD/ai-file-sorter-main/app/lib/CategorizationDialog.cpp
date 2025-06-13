#include <iostream>
#include <glib.h>
#include <gtk/gtk.h>
#include <gtk/gtkwidget.h>
#include <gtk/gtkdialog.h>
#include <gtk/gtkentry.h>
#include <filesystem>
#include <CategorizationDialog.hpp>
#include <MovableCategorizedFile.hpp>
#include <DatabaseManager.hpp>
#include <Types.hpp>


CategorizationDialog::CategorizationDialog(DatabaseManager* db_manager, gboolean show_subcategory_col)
    : db_manager(db_manager), show_subcategory_col(show_subcategory_col)
{
    builder = gtk_builder_new();
    if (!builder) {
        g_critical("Failed to initialize GtkBuilder.");
        return;
    }
    GError *error = NULL;
    if (!gtk_builder_add_from_resource(builder, "/net/quicknode/AIFileSorter/ui/sort_confirm.glade", &error)) {
        g_critical("Failed to load resource: %s", error->message);
        g_error_free(error);
        if (builder) {
            g_object_unref(builder);
            builder = nullptr;
        }
        return;
    }

    dialog = GTK_DIALOG(gtk_builder_get_object(builder, "categorization_dialog"));
    if (!dialog) {
        g_critical("Dialog widget 'categorization_dialog' not found in builder.");
    } else if (!GTK_IS_DIALOG(dialog)) {
        g_warning("'categorization_dialog' is not a valid GtkDialog.");
    }

    gtk_window_set_default_size(GTK_WINDOW(dialog), 1200, 1000);
    gtk_window_set_resizable(GTK_WINDOW(dialog), TRUE);

    treeview = GTK_TREE_VIEW(gtk_builder_get_object(builder, "file_category_treeview"));
    if (!treeview) {
        throw std::runtime_error("Error: file_category_treeview not found.");
    }

    if (!GTK_IS_CONTAINER(treeview)) {
        g_print("Tree view is not a valid container.\n");
    }

    // Set up the list store with columns (File Name, File Type, Icon, Category, Subcategory, Sorted Status Icon)
    liststore = gtk_list_store_new(6, 
                                   G_TYPE_STRING,  // File Name
                                   G_TYPE_STRING,  // File Type (Hidden "F" or "D")
                                   G_TYPE_STRING,  // Icon name
                                   G_TYPE_STRING,  // Category
                                   G_TYPE_STRING,  // Subcategory
                                   G_TYPE_STRING   // Sorted status icon (empty, checkmark, or cross)
    );
    gtk_tree_view_set_model(treeview, GTK_TREE_MODEL(liststore));

    setup_treeview_columns();
    
    confirm_button = GTK_BUTTON(gtk_builder_get_object(builder, "confirm_button"));
    continue_button = GTK_BUTTON(gtk_builder_get_object(builder, "continue_button"));

    if (!confirm_button || !continue_button) {
        g_error("Failed to load dialog buttons from builder");
        return;
    }

    g_signal_connect(confirm_button, "clicked", G_CALLBACK(+[](GtkButton *, gpointer user_data) {
        CategorizationDialog *dlg = static_cast<CategorizationDialog*>(user_data);
        dlg->on_confirm_and_sort_button_clicked();
    }), this);

    g_signal_connect(continue_button, "clicked", G_CALLBACK(+[](GtkButton *, gpointer user_data) {
        CategorizationDialog *dlg = static_cast<CategorizationDialog*>(user_data);
        dlg->on_continue_later_button_clicked();
    }), this);

    g_signal_connect(dialog, "delete-event", G_CALLBACK(+[](GtkWidget *widget, GdkEvent *event, gpointer user_data) {
        CategorizationDialog *dlg = static_cast<CategorizationDialog*>(user_data);
        return dlg->on_dialog_close(widget, event, user_data);
    }), this);
}


bool CategorizationDialog::is_dialog_valid() const {
    return dialog && GTK_IS_DIALOG(dialog);
}


void CategorizationDialog::setup_close_button() {
    close_button = GTK_BUTTON(gtk_button_new_with_label("Close"));
    gtk_widget_set_name(GTK_WIDGET(close_button), "close_button");

    GtkWidget* button_box = GTK_WIDGET(gtk_builder_get_object(builder, "button_box"));
    if (button_box) {
        gtk_container_add(GTK_CONTAINER(button_box), GTK_WIDGET(close_button));
        gtk_widget_show(GTK_WIDGET(close_button));
    }

    g_signal_connect(close_button, "clicked", G_CALLBACK(+[](GtkButton *, gpointer user_data) {
        GtkWidget* dialog = GTK_WIDGET(user_data);
        gtk_widget_destroy(dialog);
    }), dialog);
}


void CategorizationDialog::setup_treeview_columns()
{
    if (!dialog) {
        throw std::runtime_error("Dialog not initialized.");
    }

    // Get treeview dynamically from dialog
    GtkTreeView *treeview = GTK_TREE_VIEW(gtk_builder_get_object(builder, "file_category_treeview"));
    if (!treeview) {
        throw std::runtime_error("Treeview not found in dialog.");
    }

    // Detach the model before configuring columns
    gtk_tree_view_set_model(treeview, nullptr);

    // Remove existing columns
    while (gtk_tree_view_get_n_columns(treeview) > 0) {
        GtkTreeViewColumn *column = gtk_tree_view_get_column(treeview, 0);
        gtk_tree_view_remove_column(treeview, column);
    }

    GtkTreeViewColumn *column;
    GtkCellRenderer *renderer;

    // Column 0: File Name
    renderer = gtk_cell_renderer_text_new();
    column = gtk_tree_view_column_new_with_attributes("File", renderer, "text", 0, nullptr);
    gtk_tree_view_column_set_resizable(column, TRUE);
    gtk_tree_view_column_set_sizing(column, GTK_TREE_VIEW_COLUMN_AUTOSIZE);
    gtk_tree_view_insert_column(treeview, column, -1);

    // Column 1: File Type (Hidden)
    renderer = gtk_cell_renderer_text_new();
    column = gtk_tree_view_column_new_with_attributes("File Type Hidden", renderer, "text", 1, nullptr);
    gtk_tree_view_column_set_visible(column, FALSE);
    gtk_tree_view_insert_column(treeview, column, -1);

    // Column 2: File Type Icon
    renderer = gtk_cell_renderer_pixbuf_new();
    column = gtk_tree_view_column_new_with_attributes("Type", renderer, "icon-name", 2, nullptr);
    gtk_tree_view_insert_column(treeview, column, -1);

    // Column 3: Category (Editable)
    GtkCellRendererText *renderer_category = GTK_CELL_RENDERER_TEXT(gtk_cell_renderer_text_new());
    g_object_set(renderer_category, "editable", TRUE, NULL);
    g_signal_connect(renderer_category, "edited", G_CALLBACK(+[](GtkCellRendererText *renderer, gchar *path_string, gchar *new_text, gpointer user_data) {
        CategorizationDialog *dialog = static_cast<CategorizationDialog *>(user_data);
        dialog->on_category_cell_edited(renderer, path_string, new_text, dialog->liststore);
    }), this);

    column = gtk_tree_view_column_new_with_attributes("Category", GTK_CELL_RENDERER(renderer_category), "text", 3, nullptr);
    gtk_tree_view_column_set_sizing(column, GTK_TREE_VIEW_COLUMN_FIXED);
    gtk_tree_view_insert_column(treeview, column, -1);

    // Column 4: Subcategory (Editable)
    GtkCellRendererText *renderer_subcategory = GTK_CELL_RENDERER_TEXT(gtk_cell_renderer_text_new());
    g_object_set(renderer_subcategory, "editable", TRUE, NULL);
    g_signal_connect(renderer_subcategory, "edited", G_CALLBACK(+[](GtkCellRendererText *renderer, gchar *path_string, gchar *new_text, gpointer user_data) {
        CategorizationDialog *dialog = static_cast<CategorizationDialog *>(user_data);
        dialog->on_subcategory_cell_edited(renderer, path_string, new_text, dialog->liststore);
    }), this);

    this->subcategory_column = gtk_tree_view_column_new_with_attributes("Subcategory", GTK_CELL_RENDERER(renderer_subcategory), "text", 4, nullptr);
    gtk_tree_view_column_set_visible(subcategory_column, show_subcategory_col);
    gtk_tree_view_column_set_sizing(subcategory_column, GTK_TREE_VIEW_COLUMN_FIXED);
    gtk_tree_view_insert_column(treeview, subcategory_column, -1);

    // Column 5: Sorted Status Icon
    renderer = gtk_cell_renderer_pixbuf_new();
    column = gtk_tree_view_column_new_with_attributes("Sorted", renderer, "icon-name", 5, nullptr);
    gtk_tree_view_column_set_sizing(column, GTK_TREE_VIEW_COLUMN_FIXED);
    gtk_tree_view_insert_column(treeview, column, -1);

    // Reattach the model after configuring columns
    gtk_tree_view_set_model(treeview, GTK_TREE_MODEL(liststore));
}


void CategorizationDialog::on_continue_later_button_clicked()
{
    record_categorization_to_db();
    gtk_widget_destroy(GTK_WIDGET(dialog));
}


gboolean CategorizationDialog::on_dialog_close(GtkWidget *widget, GdkEvent *event, gpointer user_data) {
    record_categorization_to_db();
    return FALSE;
}


void CategorizationDialog::show_results(
    const std::vector<CategorizedFile>& categorized_files)
{
    this->categorized_files = categorized_files;

    gtk_list_store_clear(liststore);

    for (const auto& file : categorized_files) {
        GtkTreeIter iter;
        gtk_list_store_append(liststore, &iter);

        gtk_list_store_set(liststore, &iter,
                           0, file.file_name.c_str(),
                           1, (file.type == FileType::Directory) ? "D" : "F",
                           2, (file.type == FileType::Directory) ? "folder" : "text-x-script", // Icon,
                           3, file.category.c_str(),
                           4, file.subcategory.c_str(),
                           5, "",                         // Sorted Status Icon placeholder
                           -1);
    }

    gtk_widget_show_all(GTK_WIDGET(dialog));

    int result = gtk_dialog_run(dialog);
    if (result == GTK_RESPONSE_OK) {
        record_categorization_to_db();
    }

    gtk_widget_destroy(GTK_WIDGET(dialog));
}


std::vector<std::tuple<std::string, std::string, std::string, std::string>>
CategorizationDialog::get_categorized_files_from_treeview()
{
    GtkTreeModel *model = gtk_tree_view_get_model(GTK_TREE_VIEW(treeview));
    GtkTreeIter iter;
    gboolean valid = gtk_tree_model_get_iter_first(model, &iter);
    std::vector<std::tuple<std::string, std::string, std::string, std::string>> categorized_files;

    while (valid) {
        gchar *file_name;
        gchar *file_type;    // Holds "F" or "D" values
        gchar *category;
        gchar *subcategory;

        gtk_tree_model_get(model, &iter,
                           0, &file_name,
                           1, &file_type,     // Hidden
                           3, &category,
                           4, &subcategory,
                           -1);

        categorized_files.emplace_back(file_name, file_type, category, subcategory);

        g_free(file_name);
        g_free(file_type);
        g_free(category);
        g_free(subcategory);

        valid = gtk_tree_model_iter_next(model, &iter);
    }
    return categorized_files;
}


void CategorizationDialog::on_confirm_and_sort_button_clicked()
{
    record_categorization_to_db();

    auto files = get_categorized_files_from_treeview();
    std::vector<std::string> files_not_moved;

    if (!categorized_files.empty()) {
        std::string dir_path = std::filesystem::path(categorized_files[0].file_path).string();

        GtkTreeIter iter;
        gboolean valid = gtk_tree_model_get_iter_first(GTK_TREE_MODEL(liststore), &iter);
        for (const auto& [file_name, file_type, category, subcategory] : files) {
            // g_print("Processing file: %s\n", file_name.c_str());

            MovableCategorizedFile categorizedFile(dir_path, category, subcategory, file_name, file_type);

            categorizedFile.create_cat_dirs(show_subcategory_col);
            if (categorizedFile.move_file(show_subcategory_col)) {
                const gchar *sorted_icon = "emblem-default";
                gtk_list_store_set(liststore, &iter, 5, sorted_icon, -1);
                g_print("File %s moved successfully.\n", file_name.c_str());
            } else {
                const gchar *sorted_icon = "process-stop";
                gtk_list_store_set(liststore, &iter, 5, sorted_icon, -1);
                files_not_moved.push_back(file_name);
                g_print("File %s already exists in the destination.\n", file_name.c_str());
            }
            valid = gtk_tree_model_iter_next(GTK_TREE_MODEL(liststore), &iter);
            if (!valid) break;
        }
    } else {
        g_print("Error: categorized_files is empty.\n");
        return;
    }

    // g_print("Finished file move operations\n");

    if (files_not_moved.empty()) {
        // g_print("All files have been sorted and moved successfully.\n");
    } else {
        // g_print("The following files have not been moved because they already exist at the destination:\n");
        // for (const auto& file_name : files_not_moved) {
        //     g_print("%s\n", file_name.c_str());
        // }
    }

    show_close_button();
}


void CategorizationDialog::show_close_button()
{
    gtk_widget_hide(GTK_WIDGET(confirm_button));
    gtk_widget_hide(GTK_WIDGET(continue_button));
    setup_close_button();
}


CategorizationDialog::~CategorizationDialog() {
    if (builder) {
        g_object_unref(builder);
        builder = nullptr;
    }
}


void CategorizationDialog::on_category_cell_edited(
    GtkCellRendererText *cell, gchar *path_string, gchar *new_text, GtkListStore *liststore)
{
    GtkTreeIter iter;
    GtkTreePath *path = gtk_tree_path_new_from_string(path_string);

    if (gtk_tree_model_get_iter(GTK_TREE_MODEL(liststore), &iter, path)) {
        gtk_list_store_set(liststore, &iter, 3, new_text, -1);
    }

    gtk_tree_path_free(path);
}


void CategorizationDialog::on_subcategory_cell_edited(
    GtkCellRendererText *cell, gchar *path_string, gchar *new_text, GtkListStore *liststore)
{
    GtkTreeIter iter;
    GtkTreePath *path = gtk_tree_path_new_from_string(path_string);

    if (gtk_tree_model_get_iter(GTK_TREE_MODEL(liststore), &iter, path)) {
        gtk_list_store_set(liststore, &iter, 4, new_text, -1);
    }

    gtk_tree_path_free(path);
}


void CategorizationDialog::record_categorization_to_db()
{
    auto files = get_categorized_files_from_treeview();
    int index = 0;

    for (const auto& [file_name, file_type, category, subcategory] : files) {
        std::string full_file_path = categorized_files[index].file_path;
        std::string dir_path = std::filesystem::path(full_file_path).string();
        db_manager->insert_or_update_file_with_categorization(file_name, file_type, dir_path, category, subcategory);
        index++;
    }
}