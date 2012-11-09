
============
Introduction
============

This section contains an introduction to *django-powerdns-manager*, including general
information about how to submit bug reports and make feature requests.

django-powerdns-manager is a web based PowerDNS_ administration panel.

.. _PowerDNS: http://www.powerdns.com

Licensed under the *Apache License version 2.0*. More licensing information
exists in the license_ section.


Features
========

- Web based administration interface based on the admin Django app.
- Easy management of all records of a zone from a signle web page.
- Support for multiple users.
- Database schema is DNSSEC enabled.
- Automatic zone-rectify support using native python code.
- The application can be configured to support a user-defined subset of the
  resource records supported by PowerDNS and customize the order in which they
  appear in the administration panel.
- Zone file import through web form (experimental).
- Zone file export (experimental).
- Command-line interfaces to import and export zones in bulk (experimental).
- Support for secure updating of dynamic IP addresses in A and AAAA records
  over HTTP.
- Supports using a dedicated database to store the tables needed by PowerDNS.
  This database may use a different backend than the main database of the
  Django project.
- Contains demo project for quick start and experimentation.


Documentation
=============

Apart from the `django-powerdns-manager Online Documentation`_, more information about the
installation, configuration and usage of this application may be available
at the project's wiki_.

.. _`django-powerdns-manager Online Documentation`: http://packages.python.org/django-powerdns-manager
.. _wiki: http://www.codetrax.org/projects/django-powerdns-manager/wiki


Donations
=========

This software is released as free-software and provided to you at no cost. However,
a significant amount of time and effort has gone into developing this software
and writing this documentation. So, the production of this software has not
been free from cost. It is highly recommended that, if you use this software
*in production*, you should consider making a donation.

To make a donation, please visit the CodeTRAX `donations page`_ which contains
a PayPal_ *donate* button.

Thank you for considering making a donation to django-powerdns-manager.

.. _`donations page`: https://source.codetrax.org/donate.html
.. _PayPal: https://www.paypal.com


Bugs and feature requests
=========================

In case you run into any problems while using this application or think that
a new feature should be implemented, it is highly recommended you submit_ a new
report about it at the project's `issue tracker`_.

Using the *issue tracker* is the recommended way to notify the authors about
bugs or make feature requests. Also, before submitting a new report, please
make sure you have read the `new issue guidelines`_.

.. _submit: http://www.codetrax.org/projects/django-powerdns-manager/issues/new
.. _`issue tracker`: http://www.codetrax.org/projects/django-powerdns-manager/issues
.. _`new issue guidelines`: http://www.codetrax.org/NewIssueGuidelines


Support
=======

CodeTRAX does not provide support for django-powerdns-manager.

You can still get community support at the `Community Support Forums`_:

.. _`Community Support Forums`: http://www.codetrax.org/projects/django-powerdns-manager/boards


License
=======

Copyright 2012 George Notaras <gnot [at] g-loaded.eu>

Licensed under the *Apache License, Version 2.0* (the "*License*");
you may not use this file except in compliance with the License.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the License exists in the product distribution; the *LICENSE* file.
For copyright and other important notes regarding this release please read
the *NOTICE* file.
