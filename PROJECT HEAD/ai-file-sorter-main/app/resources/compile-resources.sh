glib-compile-resources resources.xml --target=resources.gresource --generate
gresource list resources.gresource
glib-compile-resources resources.xml --target=resources.c --generate-source