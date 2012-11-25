
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


Using a dedicated database for your DNS server
==============================================

It is highly recommended to configure django-powerdns-manager to use a
different database than the rest of the apps of the Django project for
security and performance reasons.

The ``PowerdnsManagerDbRouter`` database router is provided for this
purpose. All you need to do, is configure an **extra database** in
``settings.py`` named ``powerdns`` and add this router to the
``DATABASE_ROUTERS`` list.

The following example assumes using SQLite databases, but your are free to
use any database backend you want, provided that it is also supported by
the PowerDNS server software::

    DATABASES = {
        'default': {    # Used by all apps of the Django project except django-powerdns-manager
            'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'main.db',               # Or path to database file if using sqlite3.
            'USER': '',                      # Not used with sqlite3.
            'PASSWORD': '',                  # Not used with sqlite3.
            'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        },
        'powerdns': {    # Used by django-powerdns-manager and PowerDNS server
            'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'powerdns.db',           # Or path to database file if using sqlite3.
            'USER': '',                      # Not used with sqlite3.
            'PASSWORD': '',                  # Not used with sqlite3.
            'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        }
    }

    DATABASE_ROUTERS = ['powerdns_manager.routers.PowerdnsManagerDbRouter']

The configuration above indicates that ``main.db`` will be used by all
the apps of the Django project, except ``django-powerdns-manager``. The
``powerdns.db`` database will **only** be used by ``django-powerdns-manager``.

PowerDNS should also be configured to send queries to ``powerdns.db``.


Synchronize the project databases
---------------------------------

Finally, synchronize the project's databases using the following command::

    python manage.py syncdb
    python manage.py syncdb --database=powerdns


URLS
====

Add the ``powerdns_manager`` specific URL patterns to the ``urls.py`` file of
your project::

    # URLs for powerdns_manager
    urlpatterns += patterns('',
        url('^powerdns/', include('powerdns_manager.urls')),
    )


Load default group
==================

This step is **optional**.

*django-powerdns-manager* supports multiple users. Before non-superusers are
able to add DNS data, a superuser must grant them permission to do so. In a
typical Django project this is done by assigning the required permissions
directly to the users or to a group, which the users are member of.

*django-powerdns-manager* facilitates this process by providing a default group,
named *PowerDNS Managers*, which has all the required permissions to add DNS
information to the database with the exception of permissions to add/change/delete
supermaster servers. Managing data of the *supermasters* table is left by
default to Django superusers.

To load this default group run the following command::

    python manage.py loaddata default_pdns_groups

Please not that the *default_pdns_groups* fixture is primary key agnostic so
as to be imported without issues.


Settings reference 
==================

The following settings can be specified in the Django project's ``settings``
module to customize the functionality of *django-powerdns-manager*.

``PDNS_ENABLED_RR_TYPES``
    This setting holds a list of enabled resource record types for PowerDNS
    Manager. By default, it contains all the record types PowerDNS supports_.
    Enable what you need. The order of the list items defines the order that
    the sections of the record change forms appear in the administration
    interface. Example::
    
        PDNS_ENABLED_RR_TYPES = [
            'SOA',
            'NS',
            'MX',
            'A',
            'AAAA',
            'CNAME',
            'PTR',
            'TXT',
            'SPF',
            'SRV',
            'CERT',
            'DNSKEY',
            'DS',
            'KEY',
            'NSEC',
            'RRSIG',
            'HINFO',
            'LOC',
            'NAPTR',
            'RP',
            'AFSDB',
            'SSHFP',
        ]
    
``PDNS_DEFAULT_ZONE_TYPE``
    Sets the zone type that will be set as default in zone type selector box
    in the zone edit form. By default, this is set to ``NATIVE``. Example::
    
        PDNS_DEFAULT_ZONE_TYPE = 'MASTER'

``PDNS_DEFAULT_RR_TTL``
    Each resource record has Time-To-Live (TTL) information, which can be set
    by the user. In case the user does not provide this information, the
    minimum TTL setting is retrieved from the SOA record. If a SOA record
    does not exist, then the value of ``PDNS_DEFAULT_RR_TTL`` is used. By
    default, this is set to 86400 seconds. Example::
    
        PDNS_DEFAULT_RR_TTL = 3600
    
``PDNS_IS_SLAVE``
    Can be ``True`` or ``False``. Currently has not effect.

.. _supports: http://doc.powerdns.com/types.html


