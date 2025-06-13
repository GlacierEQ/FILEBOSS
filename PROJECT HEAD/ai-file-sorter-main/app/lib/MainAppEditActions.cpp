#include "MainAppEditActions.hpp"


void MainAppEditActions::on_paste(GtkEntry* path_entry) {
    GtkEditable* editable = GTK_EDITABLE(path_entry);
    gchar* clipboard_text = gtk_clipboard_wait_for_text(gtk_clipboard_get(GDK_SELECTION_CLIPBOARD));

    if (clipboard_text) {
        gint cursor_pos = gtk_editable_get_position(editable);
        gtk_editable_insert_text(editable, clipboard_text, -1, &cursor_pos);
        g_free(clipboard_text);
    }
}


void MainAppEditActions::on_copy(GtkEntry* path_entry) {
    GtkEditable* editable = GTK_EDITABLE(path_entry);
    gchar* selected_text = get_and_delete_selection(editable, FALSE);

    if (selected_text) {
        copy_to_clipboard(selected_text);
        g_free(selected_text);
    }
}


void MainAppEditActions::on_cut(GtkEntry* path_entry) {
    GtkEditable* editable = GTK_EDITABLE(path_entry);
    gchar* selected_text = get_and_delete_selection(editable, TRUE); // Explicitly pass TRUE

    if (selected_text) {
        copy_to_clipboard(selected_text);
        g_free(selected_text);
    }
}


void MainAppEditActions::on_delete(GtkEntry* path_entry) {
    GtkEditable* editable = GTK_EDITABLE(path_entry);
    get_and_delete_selection(editable, TRUE); // Explicitly pass TRUE to delete the selection
}


void MainAppEditActions::copy_to_clipboard(const gchar* text)
{
    if (text) {
        gtk_clipboard_set_text(gtk_clipboard_get(GDK_SELECTION_CLIPBOARD), text, -1);
    }
}


gchar* MainAppEditActions::get_and_delete_selection(GtkEditable* editable, gboolean delete_selection = TRUE)
{
    gint start, end;

    if (gtk_editable_get_selection_bounds(editable, &start, &end)) {
        gchar* selected_text = gtk_editable_get_chars(editable, start, end);

        if (delete_selection) {
            gtk_editable_delete_text(editable, start, end);
        }

        return selected_text; // Caller must free this
    }

    return nullptr; // No selection
}