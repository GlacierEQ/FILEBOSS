#ifndef MAIN_APP_ABOUT_HPP
#define MAIN_APP_ABOUT_HPP

#include <gtk/gtk.h>

class MainAppHelpActions {
public:
    static void show_about(GtkWindow *parent);
    static void on_tab_switched(GtkNotebook *notebook, GtkWidget *page, guint page_num, gpointer user_data);
};

#endif