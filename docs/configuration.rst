
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


Synchronize the project database
================================

Finally, synchronize the project's database using the following command::

    python manage.py syncdb

