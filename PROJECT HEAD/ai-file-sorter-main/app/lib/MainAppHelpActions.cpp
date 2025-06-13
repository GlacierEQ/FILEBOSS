#include "MainAppHelpActions.hpp"
#include <gtk/gtkcontainer.h>
#include <string>
#include <app_version.hpp>


void MainAppHelpActions::show_about(GtkWindow *parent)
{
    // Create a custom dialog
    GtkWidget *dialog = gtk_dialog_new_with_buttons(
        "About QN AI File Sorter",    // Title
        parent,                       // Parent window
        GTK_DIALOG_MODAL,             // Dialog flag
        "Close",                      // Button text
        GTK_RESPONSE_CLOSE,           // Response ID
        NULL                          // End of button list
    );

    // Set dialog size and style
    gtk_window_set_default_size(GTK_WINDOW(dialog), 600, 400);

    // Create a notebook for the tabs
    GtkWidget *notebook = gtk_notebook_new();
    gtk_notebook_set_tab_pos(GTK_NOTEBOOK(notebook), GTK_POS_TOP);
    gtk_box_pack_start(GTK_BOX(gtk_dialog_get_content_area(GTK_DIALOG(dialog))), notebook, TRUE, TRUE, 0);

    // --- "About" tab ---
    GtkWidget *about_tab_content = gtk_box_new(GTK_ORIENTATION_VERTICAL, 10);

    // Add logo to the "About" tab
    GError *error = NULL;
    GdkPixbuf *pixbuf_al = gdk_pixbuf_new_from_resource("/net/quicknode/AIFileSorter/images/logo.png", &error);
    if (!pixbuf_al) {
        g_critical("Failed to load resource: %s", error->message);
        g_clear_error(&error);
    } else {
        GtkWidget *app_logo = gtk_image_new_from_pixbuf(pixbuf_al);
        gtk_box_pack_start(GTK_BOX(about_tab_content), app_logo, FALSE, FALSE, 10);
        g_object_unref(pixbuf_al);
    }

    // Add program details to the "About" tab
    GtkWidget *program_name = gtk_label_new("QN AI File Sorter");
    
    std::string version_text = "Version: " + APP_VERSION.to_string();
    GtkWidget *version = gtk_label_new(version_text.c_str());

    GtkWidget *copyright = gtk_label_new("© 2024-2025 QuickNode. All rights reserved.");
    GtkWidget *website = gtk_link_button_new_with_label("https://www.filesorter.app", "Visit the Website");

    gtk_box_pack_start(GTK_BOX(about_tab_content), program_name, FALSE, FALSE, 5);
    gtk_box_pack_start(GTK_BOX(about_tab_content), version, FALSE, FALSE, 5);
    gtk_box_pack_start(GTK_BOX(about_tab_content), copyright, FALSE, FALSE, 5);
    gtk_box_pack_start(GTK_BOX(about_tab_content), website, FALSE, FALSE, 5);

    // Add the "About" tab to the notebook
    GtkWidget *about_label = gtk_label_new("About");
    gtk_notebook_append_page(GTK_NOTEBOOK(notebook), about_tab_content, about_label);

    // --- "Credits" tab ---
    GtkWidget *credits_tab_content = gtk_box_new(GTK_ORIENTATION_VERTICAL, 10);

    // Add logo to the "Credits" tab    
    GdkPixbuf *pixbuf_cl = gdk_pixbuf_new_from_resource("/net/quicknode/AIFileSorter/images/qn_logo.png", &error);
    if (!pixbuf_cl) {
        g_critical("Failed to load resource: %s", error->message);
        g_clear_error(&error);
    } else {
        GtkWidget *credits_logo = gtk_image_new_from_pixbuf(pixbuf_cl);
        gtk_box_pack_start(GTK_BOX(credits_tab_content), credits_logo, FALSE, FALSE, 10);
        g_object_unref(pixbuf_cl);
    }

    // Add author's details
    const gchar *author_name = "Author: hyperfield";
    GtkWidget *author_label = gtk_label_new(author_name);
    gtk_box_pack_start(GTK_BOX(credits_tab_content), author_label, FALSE, FALSE, 5);

    // Add brand name and links
    GtkWidget *author_details = gtk_label_new(NULL);
    const gchar *author_text = "Author's brand name is <a href=\"https://quicknode.net\">QN (QuickNode)</a>.\n"
                               "Source code on Github is <a href=\"https://github.com/hyperfield/ai-file-sorter\">here.</a>";
    gtk_label_set_markup(GTK_LABEL(author_details), author_text);
    gtk_label_set_line_wrap(GTK_LABEL(author_details), TRUE);
    gtk_box_pack_start(GTK_BOX(credits_tab_content), author_details, FALSE, FALSE, 5);

    // Add the "Credits" tab to the notebook
    GtkWidget *credits_label = gtk_label_new("Credits");
    gtk_notebook_append_page(GTK_NOTEBOOK(notebook), credits_tab_content, credits_label);

    // Show dialog
    gtk_widget_show_all(dialog);
    gtk_dialog_run(GTK_DIALOG(dialog));
    gtk_widget_destroy(dialog);
}