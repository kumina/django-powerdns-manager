
=============
Configuration
=============

This section contains information about how to configure your Django projects
to use *django-powerdns-manager* and also contains a quick reference of the available
*settings* that can be used in order to customize the functionality of this
application.


Configuring your project
========================

In the Django project's ``settings`` module, add ``powerdns_manager`` to the
``INSTALLED_APPS`` setting::

    INSTALLED_APPS = (
        ...
        'powerdns_manager',
    )


Reference of the application settings
=====================================

The following settings can be specified in the Django project's ``settings``
module to customize the functionality of *django-powerdns-manager*.

``SETTING_A``
    Setting A ...


URLS
====

Finally, edit the ``urls.py`` file of your project to add powerdns_manager's urls::

    # URLs for powerdns_manager
    urlpatterns += patterns('',
        url('^powerdns/', include('powerdns_manager.urls')),
    )
    

Synchronize the project database
================================

Finally, synchronize the project's database using the following command::

    python manage.py syncdb

