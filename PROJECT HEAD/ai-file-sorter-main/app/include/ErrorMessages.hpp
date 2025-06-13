#ifndef ERRORMESSAGES_H
#define ERRORMESSAGES_H

#include <libintl.h>

#define _(String) gettext(String)

#define ERR_NO_FILES_TO_CATEGORIZE _("There are no files or directories to categorize.")
#define ERR_INVALID_PATH _("Invalid directory path.")
#define ERR_NO_INTERNET_CONNECTION _("No internet connection. Please check your network and try again.")

#endif