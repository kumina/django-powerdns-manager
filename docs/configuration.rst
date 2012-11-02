
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


URLS
====

Add the ``powerdns_manager`` specific URL patterns to the ``urls.py`` file of
your project::

    # URLs for powerdns_manager
    urlpatterns += patterns('',
        url('^powerdns/', include('powerdns_manager.urls')),
    )


Synchronize the project database
================================

Finally, synchronize the project's database using the following command::

    python manage.py syncdb

