
=====
Usage
=====

This section contains information, including examples, about how to use
*django-powerdns-manager* in your existing Django projects or applications.


Using the Web Administration Interface
======================================

*django-powerdns-manager* uses the *admin* Django app to provide an
administration interface. The layout is that of a typical Django project.

All resource records, domain metadata and crypto keys that belong to a specific
zone are managed from a single web page.

Here are some guidelines when entering DNS data::

- All hostnames must be FQDN and should be entered without a trailing dot.
- TTL and other time information should be entered in seconds.
- Strings, for instance in TXT records, must not be enclosed in double quotes.
 

Concept of Dynamic Zones
========================

Apart from updating records using the DNS UPDATE query, *django-powerdns-manager*
supports updating the IP address of A and AAAA records over HTTP.

For this to happen it is mandatory to add the zone to the Dynamic Zones table.
Once a reference for a zone is in that table, an API key will be generated,
which can be used to get authorization to update A and AAAA records over HTTP.

TODO

IP Updates over HTTP
====================

Supported arguments

``api_key``
    Should be equal to the generated API key that exists in the zone record
    in the DynamicZones table. *Mandatory* - no default.
``hostname``
    Should contain the hostname of the A or AAAA record you want to update.
    This is an *optional* setting. If omitted, all A and AAAA records of the
    zone are updated, if an IP address is provided or guessed.
``ipv4``
    Should contain an IPv4 address. This is *optional*. If omitted, the
    remote client's IP address, if it is an IPv4 address, is used.
``ipv6``
    Should contain an IPv6 address. This is *optional*. If omitted, the
    remote client's IP address, if it is an IPv6 address, is used.
    
Example request using ``curl``::

    curl -k \
        -F "api_key=UBSE1RJ0J175MRAMJC31JFUH" \
        -F "hostname=ns1.centos.example.org" \
        -F "ipv4=10.1.2.3" \
        -F "ipv6=3ffe:1900:4545:3:200:f8ff:fe21:67cf" \
        https://192.168.0.101/powerdns/update/

TODO

RESTful API version 1
=====================
The REST API version 1 a very simple, non-JSON API that allows the external
party to CRUD records. A second API allows the external party to change zone
settings.

To access the API, an apikey needs to be supplied via the ``X-PDNS-APIKEY`` HTTP
header.

HTTP Methods supported
----------------------

``GET``
  This returns all records matching the name, type and content (see below for
  filtering options).
``POST``
  This request allows the creation of records. Use parameters and options to 
  set the correct data (see below).
``DELETE``
  Delete records matching the parameters.
``PUT``
  Update the ttl or content of a single record.

Request syntax
--------------

    /api_v1/records/NAME[/TYPE][.FORMAT]

``NAME``
  The name associated with the the record (e.g. www.example.net) *mandatory*.
``TYPE``
  The type of the records (e.g. A, AAAA, CNAME etc.). It is *mandatory* for
  POST requests and *optional* for the other requests.
``FORMAT``
  The preferred output format of the response. There is only one possible
  value: zone. On a succesful request, the records are returned.

The API accepts several parameters:

``content_match``and ``content_search``
  Useful with GET, PUT and DELETE, they will filter on the content of the
  records. content_match means 'exacts match', whereas content_search means
  'substring'.
``content_set`` and ``ttl_set``
  These parameters are useful with PUT and POST request. They set the content
  and ttl of the record respectively.

Examples
--------
Adding a record::

    curl -X POST \
    -H 'X-PDNS-APIKEY: FFFFFFFFFFFFFFFFFFFFFFFF' \
    "https://dnsadmin/powerdns/api_v1/records/www.example.net/A?content_set=1.2.3.4"

Updating the created record::

    curl -X PUT \
    -H 'X-PDNS-APIKEY: FFFFFFFFFFFFFFFFFFFFFFFF' \
    "https://dnsadmin/powerdns/api_v1/records/www.example.net/A?content_match=1.2.3.4&content_set=2.3.4.5&ttl_set=1200"

Deleting all A records for www.example.net::

    curl -X DELETE \
    -H 'X-PDNS-APIKEY: FFFFFFFFFFFFFFFFFFFFFFFF' \
    "https://dnsadmin/powerdns/api_v1/records/www.example.net/A"

Deleting all records for www.example.net::

    curl -X DELETE \
    -H 'X-PDNS-APIKEY: FFFFFFFFFFFFFFFFFFFFFFFF' \
    "https://dnsadmin/powerdns/api_v1/records/www.example.net"

Import zone files
=================

To import by pasting zonefile data::

    https://192.168.0.101/powerdns/import/zonefile/

To import by using ACFR query::

    https://192.168.0.101/powerdns/import/axfr/

TODO


Export zone files
=================

Visit::

    https://192.168.0.101/powerdns/export/domain.tld/
    
Replace ``domain.tld`` with the zone origin you want to export.

TODO


Zone Cloning
============

TODO

