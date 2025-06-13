#ifndef MAIN_APP_EDIT_ACTIONS_HPP
#define MAIN_APP_EDIT_ACTIONS_HPP

#include <gtk/gtk.h>

class MainAppEditActions {
public:
    static void on_paste(GtkEntry *path_entry);
    static void on_copy(GtkEntry *path_entry);
    static void on_cut(GtkEntry *path_entry);
    static void on_delete(GtkEntry *path_entry);

private:
    static void copy_to_clipboard(const gchar *text);
    static gchar *get_and_delete_selection(GtkEditable *editable,
                                           gboolean delete_selection);
};

#endif