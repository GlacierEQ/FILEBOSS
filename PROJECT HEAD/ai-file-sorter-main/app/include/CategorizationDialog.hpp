#include <DatabaseManager.hpp>
#include <gtk/gtk.h>


class CategorizationDialog
{
public:
    CategorizationDialog(DatabaseManager* db_manager, gboolean show_subcategory_col);
    ~CategorizationDialog();

    bool is_dialog_valid() const;
    void show();
    void show_results(const std::vector<CategorizedFile>& categorized_files);
    void on_confirm_and_sort_button_clicked();

private:
    GtkDialog *dialog;
    GtkButton *confirm_button;
    GtkButton *continue_button;
    GtkButton *close_button;
    GtkTreeView *treeview;
    GtkListStore *liststore;
    GtkBuilder *builder;
    const char* categorization_db;
    DatabaseManager* db_manager;
    std::vector<CategorizedFile> categorized_files;
    GtkTreeViewColumn* subcategory_column;
    gboolean show_subcategory_col;

    void on_confirm_button_clicked();
    void on_continue_later_button_clicked();
    void setup_treeview_columns();
    void on_category_cell_edited(GtkCellRendererText *cell, gchar *path_string, gchar *new_text, GtkListStore *liststore);
    void on_subcategory_cell_edited(GtkCellRendererText *cell, gchar *path_string, gchar *new_text, GtkListStore *liststore);
    void record_categorization_to_db();
    void on_category_edited(GtkCellRendererText *renderer, gchar *path, gchar *new_text, GtkTreeView *treeview);
    void setup_close_button();
    void show_close_button();
    std::vector<std::tuple<std::string, std::string, std::string, std::string>> get_categorized_files_from_treeview();
    gboolean on_dialog_close(GtkWidget *widget, GdkEvent *event, gpointer user_data);
};