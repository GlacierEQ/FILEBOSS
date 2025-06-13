    #ifndef CATEGORIZATIONPROGRESSDIALOG_HPP
    #define CATEGORIZATIONPROGRESSDIALOG_HPP

    #include <gtkmm.h>
    #include <thread>
    #include <atomic>

    class MainApp;

    class CategorizationProgressDialog
    {
    public:
        MainApp* m_MainApp;

        CategorizationProgressDialog(GtkWindow* parent, MainApp *main_app, gboolean show_subcategory_col);
        ~CategorizationProgressDialog();
        void show();
        void hide();
        void append_text(const std::string &text);        

    private:
        GtkWidget* m_Dialog;
        GtkWidget* m_TextView;
        GtkWidget* m_StopButton;
        GtkTextBuffer *buffer;

        GtkWidget* create_categorization_progress_dialog(GtkWindow* parent);
    };

    #endif