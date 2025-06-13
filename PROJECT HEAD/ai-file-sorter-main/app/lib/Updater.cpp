#include "Updater.hpp"
#include "app_version.hpp"
#include <curl/curl.h>
#include <iostream>
#include <stdexcept>
#ifdef _WIN32
    #include <json/json.h>
#elif __APPLE__
    #include <json/json.h>
#else
    #include <jsoncpp/json/json.h>
#endif
#include <optional>
#include <gtk/gtk.h>
#include <gtk/gtktypes.h>
#include <curl/easy.h>
#include <glibmm/main.h>
#include <future>


Updater::Updater(Settings& settings) 
    :
    settings(settings),
    update_spec_file_url([]
    {
        const char* url = std::getenv("UPDATE_SPEC_FILE_URL");
        if (!url) {
            throw std::runtime_error("Environment variable UPDATE_SPEC_FILE_URL is not set");
        }
        return std::string(url);
    }())
{}


void Updater::check_updates()
{
    std::string update_json = fetch_update_metadata();
    Json::CharReaderBuilder readerBuilder;
    Json::Value root;
    std::string errors;

    std::unique_ptr<Json::CharReader> reader(readerBuilder.newCharReader());
    if (!reader->parse(update_json.c_str(), update_json.c_str() + update_json.length(), &root, &errors)) {
        throw std::runtime_error("JSON Parse Error: " + errors);
    }

    if (!root.isMember("update")) {
        update_info.reset();
        return;
    }

    const Json::Value update = root["update"];
    UpdateInfo info;

    if (update.isMember("current_version") && update["current_version"].isString()) {
        info.current_version = update["current_version"].asString();
    }

    if (update.isMember("min_version") && update["min_version"].isString()) {
        info.min_version = update["min_version"].asString();
    }
    
    if (update.isMember("download_url") && update["download_url"].isString()) {
        info.download_url = update["download_url"].asString();
    }

    if (APP_VERSION >= string_to_Version(info.current_version)) {
        update_info.reset();
        return;
    }

    update_info = std::make_optional(info);  // Store the update info
}


bool Updater::is_update_available()
{
    check_updates();
    return update_info.has_value();
}


bool Updater::is_update_required()
{
    return string_to_Version(update_info.value_or(UpdateInfo()).min_version) > APP_VERSION;
}


void Updater::begin()
{
    this->update_future = std::async(std::launch::async, [this]() { 
        try {
            if (is_update_available()) {
                Glib::signal_idle().connect_once([this]() {
                    if (is_update_required()) {
                        bool is_required = true;
                        display_update_dialog(is_required);
                    } else if (!is_update_skipped()) {
                        display_update_dialog();
                    }
                });
            } else {
                Glib::signal_idle().connect_once([]() {
                    std::cout << "No updates available.\n";
                });
            }
        } catch (const std::exception &e) {
            Glib::signal_idle().connect_once([e]() {
                std::cerr << "Updater encountered an error: " << e.what() << "\n";
            });
        }
    });
}


bool Updater::is_update_skipped()
{
    Version skipped_version = string_to_Version(settings.get_skipped_version());
    return APP_VERSION <= skipped_version;
}


void Updater::display_update_dialog(bool is_required) {
    GtkWidget* dialog;
    GtkWidget* content_area;

    if (!update_info) {
        std::cerr << "No update information available.\n";
        return;
    }

    if (update_info.has_value() && is_required) {
        dialog = gtk_dialog_new_with_buttons(
            "Required Update Available", nullptr, GTK_DIALOG_MODAL,
            "Update Now", GTK_RESPONSE_ACCEPT,
            "Quit", GTK_RESPONSE_DELETE_EVENT, // Quit button
            nullptr);
        content_area = gtk_dialog_get_content_area(GTK_DIALOG(dialog));

        GtkWidget* label = gtk_label_new(
            "A required update is available. Please update to continue.\nIf you choose to quit, the application will close.");
        gtk_label_set_xalign(GTK_LABEL(label), 0.5);  // Horizontal alignment: 0.0 (left) to 1.0 (right), 0.5 is center
        gtk_label_set_justify(GTK_LABEL(label), GTK_JUSTIFY_CENTER);
        gtk_container_add(GTK_CONTAINER(content_area), label);
        
        // Add padding to the label
        gtk_widget_set_margin_start(label, 20);
        gtk_widget_set_margin_end(label, 20);
        gtk_widget_set_margin_top(label, 10);
        gtk_widget_set_margin_bottom(label, 10);

        // Disable the close button to ensure users must act explicitly
        gtk_window_set_deletable(GTK_WINDOW(dialog), false);
    } else {
        dialog = gtk_dialog_new_with_buttons(
            "Optional Update Available", nullptr, GTK_DIALOG_MODAL,
            "Update Now", GTK_RESPONSE_ACCEPT,
            "Skip This Version", GTK_RESPONSE_REJECT,
            "Cancel", GTK_RESPONSE_CANCEL,
            nullptr);
        content_area = gtk_dialog_get_content_area(GTK_DIALOG(dialog));

        GtkWidget* label = gtk_label_new(
            "An optional update is available. Would you like to update now?");
        gtk_container_add(GTK_CONTAINER(content_area), label);

        // Add padding to the label
        gtk_widget_set_margin_start(label, 20);
        gtk_widget_set_margin_end(label, 20);
        gtk_widget_set_margin_top(label, 10);
        gtk_widget_set_margin_bottom(label, 10);
    }

    // Add padding to the content area (if needed for future widgets)
    gtk_widget_set_margin_top(content_area, 10);
    gtk_widget_set_margin_bottom(content_area, 10);
    gtk_widget_set_margin_start(content_area, 10);
    gtk_widget_set_margin_end(content_area, 10);

    gtk_widget_show_all(dialog);
    gint response = gtk_dialog_run(GTK_DIALOG(dialog));

    switch (response) {
        case GTK_RESPONSE_ACCEPT: {
            std::string command;

            #ifdef __linux__
                command = "xdg-open " + update_info.value().download_url;
            #elif _WIN32
                command = "start " + update_info.value().download_url;
            #elif __APPLE__
                command = "open " + update_info.value().download_url;
            #else
                std::cerr << "Unsupported platform for opening URLs.\n";
                return;
            #endif

            int result = std::system(command.c_str());
            if (result != 0) {
                std::cerr << "Failed to open URL: " << update_info.value().download_url << std::endl;
            } else {
                std::cout << "Opening download URL: " << update_info.value().download_url << std::endl;
            }

            gtk_widget_destroy(dialog);

            if (is_required) {
                exit(EXIT_SUCCESS);
            }
            break;
        }

        case GTK_RESPONSE_DELETE_EVENT: {
            gtk_widget_destroy(dialog);

            // Exit the app only for required updates
            if (is_required) {
                exit(EXIT_SUCCESS);
            }
            break;
        }

        case GTK_RESPONSE_REJECT: {
            if (!is_required) {
                std::string skipped_version = update_info.value().current_version;
                settings.set_skipped_version(skipped_version);
                if (!settings.save()) {
                    std::cerr << "Failed to save skipped version to settings." << std::endl;
                } else {
                    std::cout << "User chose to skip version " << skipped_version << "." << std::endl;
                }
            }
            break;
        }

        case GTK_RESPONSE_CANCEL:
            if (!is_required) {
                break;
            }
            // For required updates, Cancel should not be an option.
            [[fallthrough]];

        default:
            if (!is_required) {
                std::cout << "Dialog closed with an unknown response." << std::endl;
            }
            break;
    }

    gtk_widget_destroy(dialog);
}


size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}


std::string Updater::fetch_update_metadata() const {
    CURL *curl = curl_easy_init();
    if (!curl) {
        throw std::runtime_error("Initialization Error: Failed to initialize cURL.");
    }

    CURLcode res;
    std::string response_string;

    // Set curl options
    #ifdef _WIN32
        std::string cert_path = std::filesystem::current_path().string() + "\\certs\\cacert.pem";
        curl_easy_setopt(curl, CURLOPT_CAINFO, cert_path.c_str());
    #endif

    curl_easy_setopt(curl, CURLOPT_URL, update_spec_file_url.c_str());
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_string);

    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

    // Perform the request
    res = curl_easy_perform(curl);

    // Handle errors
    if (res != CURLE_OK) {
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        throw std::runtime_error("Network Error: " + std::string(curl_easy_strerror(res)));
    }

    // Check HTTP response code
    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    if (http_code == 401) {
        throw std::runtime_error("Authentication Error: Invalid or missing API key.");
    } else if (http_code == 403) {
        throw std::runtime_error("Authorization Error: API key does not have sufficient permissions.");
    } else if (http_code >= 500) {
        throw std::runtime_error("Server Error: The server returned an error. Status code: " + std::to_string(http_code));
    } else if (http_code >= 400) {
        throw std::runtime_error("Client Error: The server returned an error. Status code: " + std::to_string(http_code));
    }

    return response_string;
}


Version Updater::string_to_Version(const std::string& version_str) {
    std::vector<int> digits;
    std::istringstream stream(version_str);
    std::string segment;

    while (std::getline(stream, segment, '.')) {
        digits.push_back(std::stoi(segment));
    }

    return Version{digits};
}


Updater::~Updater() = default;