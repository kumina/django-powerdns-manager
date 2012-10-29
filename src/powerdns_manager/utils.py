# -*- coding: utf-8 -*-
#
#  This file is part of django-powerdns-manager.
#
#  django-powerdns-manager is a web based PowerDNS administration panel.
#
#  Development Web Site:
#    - http://www.codetrax.org/projects/django-powerdns-manager
#  Public Source Code Repository:
#    - https://source.codetrax.org/hgroot/django-powerdns-manager
#
#  Copyright 2012 George Notaras <gnot [at] g-loaded.eu>
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import time
    
import dns.zone
from dns.zone import BadZone, NoSOA, NoNS, UnknownOrigin
from dns.exception import DNSException
from dns.rdataclass import *
from dns.rdatatype import *

from django.db.models.loading import cache



def process_zone_file(origin, zonetext, overwrite=False):
    """Imports zone to the database.
    
    No checks for existence are performed in this file. For form processing,
    see the ``import_zone_view`` view.
    
    *****
    Special kudos to Grig Gheorghiu for demonstrating how to manage zone files
    using dnspython in the following article:
    http://agiletesting.blogspot.com/2005/08/managing-dns-zone-files-with-dnspython.html
    *****
    
    """
    # Does not seem to be able to process unicode, so encode data to latin1
    origin = origin.encode('latin1')
    zonetext = zonetext.encode('latin1')
    zonetext = zonetext.replace('\r\n', '\n')
    
    Domain = cache.get_model('powerdns_manager', 'Domain')
    Record = cache.get_model('powerdns_manager', 'Record')
    
    try:
        zone = dns.zone.from_text(zonetext, origin=origin, relativize=False)
        if not str(zone.origin).rstrip('.'):
            raise UnknownOrigin
        
        # New zone data is now available
        
        # Check if zone already exists in the database.
        try:
            domain_instance = Domain.objects.get(name=origin)
        except Domain.DoesNotExist:
            pass    # proceed with importing the new zone data
        else:   # Zone exists
            if overwrite:
                # If ``overwrite`` has been checked, then delete the current zone.
                domain_instance.delete()
            else:
                raise Exception('Zone already exists. If you wish to replace it with the imported one, check the <em>Overwrite</em> option in the import form.')
        
        # Import the new zone data to the database.
        
        # Create a domain instance
        the_domain = Domain.objects.create(name=str(zone.origin).rstrip('.'), type='NATIVE', master='')
        
        # Create RRs
        for name, node in zone.nodes.items():
            rdatasets = node.rdatasets
            
            for rdataset in rdatasets:
                
                # Check instance variables of types:
                # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes-module.html
    
                for rdata in rdataset:
                    
                    rr = Record(
                        domain=the_domain,
                        name=str(name).rstrip('.'), # name is the dnspython node name
                        change_date=int(time.time()),
                        ttl = rdataset.ttl
                    )
                    
                    if rdataset.rdtype == SOA:
                        # Set type
                        rr.type = dns.rdatatype._by_value[SOA]  # http://www.dnspython.org/docs/1.10.0/html/dns.rdatatype-module.html#_by_value
                        # Construct content
                        rr.content = '%s %s %s %s %s %s %s' % (
                            str(rdata.mname).rstrip('.'),
                            str(rdata.rname).rstrip('.'),
                            rdata.serial,
                            rdata.refresh,
                            rdata.retry,
                            rdata.expire,
                            rdata.minimum
                        )
    
                    elif rdataset.rdtype == NS:
                        # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.ANY.NS.NS-class.html
                        rr.type = dns.rdatatype._by_value[NS]
                        rr.content = str(rdata.target).rstrip('.')
    
                    elif rdataset.rdtype == MX:
                        # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.ANY.MX.MX-class.html
                        rr.type = dns.rdatatype._by_value[MX]
                        rr.content = str(rdata.exchange).rstrip('.')
                        rr.prio = rdata.preference
                    
                    elif rdataset.rdtype == TXT:
                        # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.ANY.TXT.TXT-class.html
                        rr.type = dns.rdatatype._by_value[TXT]
                        rr.content = ' '.join(rdata.strings)
                    
                    elif rdataset.rdtype == CNAME:
                        # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.ANY.CNAME.CNAME-class.html
                        rr.type = dns.rdatatype._by_value[CNAME]
                        rr.content = str(rdata.target).rstrip('.')
                        
                    elif rdataset.rdtype == A:
                        # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.IN.A.A-class.html
                        rr.type = dns.rdatatype._by_value[A]
                        rr.content = rdata.address
                    
                    elif rdataset.rdtype == AAAA:
                        # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.IN.AAAA.AAAA-class.html
                        rr.type = dns.rdatatype._by_value[AAAA]
                        rr.content = rdata.address
                    
                    # TODO: add support for more records
                    
                    rr.save()
        
        # Rectify zone
        rectify_zone(the_domain.name)
                    

    except NoSOA:
        raise Exception('The zone has no SOA RR at its origin.')
    except NoNS:
        raise Exception('The zone has no NS RRset at its origin.')
    except UnknownOrigin:
        raise Exception('The zone\'s origin is unknown.')
    except BadZone:
        raise Exception('The zone is malformed.')
    except DNSException, e:
        #raise Exception(str(e))
        raise Exception('The zone is malformed.')



def rectify_zone(origin):
    """Fix up DNSSEC fields (order, auth).
    
    *****
    Special kudos to the folks at the #powerdns IRC channel for the help,
    especially Habbie and Maik. 
    *****
    
    rectify_zone() accepts a string containing the zone origin.
    Returns nothing.
    
    PowerDNS Documentation at Chapter 12 Section 8.5:
    
        http://doc.powerdns.com/dnssec-modes.html#dnssec-direct-database
    
    If you ever need to read this code and you are not much into DNS stuff,
    here is some information about the involved DNS Resource Records and the
    terminology used.
    
    * A: http://www.simpledns.com/help/v52/index.html?rec_a.htm
    * AAAA: http://www.simpledns.com/help/v52/index.html?rec_aaaa.htm
    * DS: http://www.simpledns.com/help/v52/index.html?rec_ds.htm
    * NS: http://www.simpledns.com/help/v52/index.html?rec_ns.htm
    
    Terminology:
    
    * Glue: Glue records are needed to prevent circular references. Circular
      references exist where the name servers for a domain can't be resolved
      without resolving the domain they're responsible for. For example, if
      the name servers for yourdomain.com are ns1.yourdomain.com and
      ns2.yourdomain.com, the DNS client would not be able to get to either
      name server without knowing where yourdomain.com is. But this information
      is held by those name servers! A glue record is a hint that is provided
      by the parent DNS server.
      More at: http://www.webdnstools.com/dnstools/articles/glue_records
    
    * Delegation: When the authoritative name server for a domain receives
      a request for a subdomain's records and responds with NS records for
      other name servers, that is DNS delegation.
    
    
    AUTH Field
    ==========
    
    The 'auth' field should be set to '1' for data for which the zone
    itself is authoritative, which includes the SOA record and its own NS
    records.
    
    The 'auth' field should be 0 however for NS records which are used for
    delegation, and also for any glue (A, AAAA) records present for this
    purpose. Do note that the DS record for a secure delegation should be
    authoritative!
    
        ~~~~ PowerDNS Documentation at Chapter 12 Section 8.5
      
    Rules used in the following code
    --------------------------------
    
    1. A & AAAA records (glue) of delegated names always get auth=0
    2. DS records (used for secure delegation) get auth=1
    3. Delegating NS records get auth=0
    
    
    ORDERNAME Field
    ===============
    
    The 'ordername' field needs to be filled out depending on the NSEC/NSEC3
    mode. When running in NSEC3 'Narrow' mode, the ordername field is ignored
    and best left empty. In NSEC mode, the ordername field should be NULL for
    any glue but filled in for delegation NS records and all authoritative
    records. In NSEC3 opt-out mode (the only NSEC3 mode PowerDNS currently
    supports), any non-authoritative records (as described for the 'auth'
    field) should have ordername set to NULL.

    In 'NSEC' mode, it should contain the relative part of a domain name,
    in reverse order, with dots replaced by spaces. So 'www.uk.powerdnssec.org'
    in the 'powerdnssec.org' zone should have 'uk www' as its ordername.

    In 'NSEC3' non-narrow mode, the ordername should contain a lowercase
    base32hex encoded representation of the salted & iterated hash of the full
    record name. pdnssec hash-zone-record zone record can be used to calculate
    this hash. 
    
        ~~~~ PowerDNS Documentation at Chapter 12 Section 8.5
    
    Rules used in the following code
    --------------------------------
    
    If no crypto keys are present for the domain, DNSSEC is not enabled,
    so the ``ordername`` field is not necessary to be filled. However, this
    function always fills the ``ordername`` field regardless of the existence
    of crypto keys in the cryptokeys table. ``pdnssec rectify-zone ...`` fills
    the ordername field regardless of the existence of keys in cryptokeys,
    so we stick to that functionality.
    
    Modes are distinguished by the following criteria:
    
    (a) domain has no DNSSEC: there are no keys in cryptokeys
    (b) domain has DNSSEC with NSEC: there are keys in cryptokeys, and nothing about NSEC3 in domainmetadata
    (c) domain has DNSSEC with narrow NSEC3: cryptokeys+NSEC3PARAM+NSEC3NARROW
    (d) domain has DNSSEC with non-narrow NSEC3: cryptokeys+NSEC3PARAM
    (e) domain has DNSSEC with opt-out NSEC3: cryptokeys+NSEC3PARAM
    
    Note: non-narrow and opt-out NSEC3 modes cannot be distinguished. All rules
    mentioned in the documentation for these two modes apply if there are
    cryptokeys+NSEC3PARAM.
    
    Note 2: there is never a case in which ordername is filled in on glue record.
    
    1) ordername in NSEC mode:
        - NULL for glue (A, AAAA) records
        - Filled for:
            a) delegation NS records
            b) all authoritative records (auth=1)
          It should contain the relative part of a domain name, in reverse
          order, with dots replaced by spaces.
          
    2) ordername in NSEC3 'Narrow' mode:
        - empty (but not NULL)
    
    3) ordername in NSEC3 'Opt-out' or 'Non-Narrow' modes:
        - NULL for non-authoritative records (auth=0)
        - lowercase base32hex encoded representation of the salted & iterated
          hash of the full record name for authoritative records (auth=1)
    
    
    EMPTY NON-TERMINALS
    ===================
    
    TODO: implement empty terminal support
    
    In addition, from 3.2 and up, PowerDNS fully supports empty non-terminals.
    If you have a zone example.com, and a host a.b.c.example.com in it,
    rectify-zone (and the AXFR client code) will insert b.c.example.com and
    c.example.com in the records table with type NULL (SQL NULL, not 'NULL').
    Having these entries provides several benefits. We no longer reply NXDOMAIN
    for these shorter names (this was an RFC violation but not one that caused
    trouble). But more importantly, to do NSEC3 correctly, we need to be able
    to prove existence of these shorter names. The type=NULL records entry
    gives us a place to store the NSEC3 hash of these names.

    If your frontend does not add empty non-terminal names to records, you will
    get DNSSEC replies of 3.1-quality, which has served many people well, but
    we suggest you update your code as soon as possible!
    
        ~~~~ PowerDNS Documentation at Chapter 12 Section 8.5
    
    """
    Domain = cache.get_model('powerdns_manager', 'Domain')
    Record = cache.get_model('powerdns_manager', 'Record')
    DomainMetadata = cache.get_model('powerdns_manager', 'DomainMetadata')
    CryptoKey = cache.get_model('powerdns_manager', 'CryptoKey')
    
    # List containing domain parts
    origin_parts = origin.split('.')
    
    # Get the Domain instance that corresponds to the supplied origin
    # TODO: Do some exception handling here in case domain does not exist
    the_domain = Domain.objects.get(name=origin)
    
    # Get a list of the zone's records
    zone_rr_list = Record.objects.filter(domain__name=origin)
    
    # Find delegated names by checking the names of all NS and DS records.
    delegated_names_list = []
    for rr in zone_rr_list:
        if rr.type not in ('NS', 'DS'):
            continue
        rr_name_parts = rr.name.split('.')
        if len(rr_name_parts) > len(origin_parts):
            # name is delegated
            if rr.name not in delegated_names_list:
                delegated_names_list.append(rr.name)
    
    
    # AUTH field management
    
    # Set auth=1 on all records initially
    for rr in zone_rr_list:
        rr.auth = True
    
    for delegated_name in delegated_names_list:
        
        # Set auth=0 to A & AAAA records (glue) of delegated names
        for rr in zone_rr_list:
            if rr.name == delegated_name and rr.type in ('A', 'AAAA'):
                rr.auth = False
    
        # DS records should already have auth=1
        
        # Set auth=0 to NS records
        for rr in zone_rr_list:
            if rr.name == delegated_name and rr.type == 'NS':
                rr.auth = False
    
    
    # ORDERNAME field management
    
    # If no crypto keys are present for the domain, DNSSEC is not enabled,
    # so the ``ordername`` field is not necessary to be filled. However, the
    # following code always fills the ``ordername`` field. 
    qs = CryptoKey.objects.filter(domain=the_domain)
    if not len(qs):
        # This is not a DNSSEC-enabled domain.
        # We still fill the ordername field as mentioned in the docstring.
        pass
    
    # Decide NSEC mode:
    try:
        nsec3 = DomainMetadata.objects.get(
            domain=the_domain, kind__startswith='NSEC3')
    except DomainMetadata.DoesNotExist:
        # NSEC Mode
        
        for rr in zone_rr_list:
            
            # Generate ordername content
            name_parts = rr.name.split('.')
            ordername_content_parts = name_parts[:-3]
            ordername_content_parts.reverse()
            ordername_content = ' '.join(ordername_content_parts)
                
            if rr.name in delegated_names_list:
            
                # Set ordername=NULL for A & AAAA records of delegated names (glue)
                if rr.type in ('A', 'AAAA'):
                    rr.ordername = None
                
                # Fill ordername for: Delegation NS records
                elif rr.type == 'NS':
                    rr.ordername = ordername_content
            
            # Fill ordername for: All auth=1 records
            if rr.auth:
                rr.ordername = ordername_content
        
    else:
        # NSEC3 Mode
        try:
            nsec3narrow = DomainMetadata.objects.get(
                domain=the_domain, kind='NSEC3NARROW')
        except DomainMetadata.DoesNotExist:
            # NSEC3 'Non-Narrow', 'Opt-out' mode
            for rr in zone_rr_list:
                if rr.auth:
                    # TODO: implement base32hex encoding
                    rr.ordername = '_base32hex_'
                else:
                    rr.ordername = None
        else:
            # NSEC3 'Narrow' Mode
            for rr in zone_rr_list:
                rr.ordername=''
    
    
    # Save the records
    # Since this is an internal maintenance function, the serial of the zone
    # is not updated.
    for rr in zone_rr_list:
        rr.save()





# Base32 encoding/decoding must be done in Python
_b32alphabet = {
    0: '0',  9: '9', 18: 'I', 27: 'R',
    1: '1', 10: 'A', 19: 'J', 28: 'S',
    2: '2', 11: 'B', 20: 'K', 29: 'T',
    3: '3', 12: 'C', 21: 'L', 30: 'U',
    4: '4', 13: 'D', 22: 'M', 31: 'V',
    5: '5', 14: 'E', 23: 'N',
    6: '6', 15: 'F', 24: 'O',
    7: '7', 16: 'G', 25: 'P',
    8: '8', 17: 'H', 26: 'Q',
    }

_b32tab = _b32alphabet.items()
_b32tab.sort()
_b32tab = [v for k, v in _b32tab]
_b32rev = dict([(v, long(k)) for k, v in _b32alphabet.items()])


def b32hex_encode(s):
    """Encode a string using Base32hex.

    s is the string to encode.  The encoded string is returned.
    
    ``base32hex`` encoding is described in Section 7 of RFC4648
    
        http://tools.ietf.org/html/rfc4648#section-7
    
    This function is licensed under the terms of the:
    
        PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
    
    It has derived from the b32encode() function of the ``base64`` module
    of the Standard Library.
    
    ``_b32alphabet`` has been updated to the alphabet that is included in
    Section 7 of RFC4648.
    
    """
    parts = []
    quanta, leftover = divmod(len(s), 5)
    # Pad the last quantum with zero bits if necessary
    if leftover:
        s += ('\0' * (5 - leftover))
        quanta += 1
    for i in range(quanta):
        # c1 and c2 are 16 bits wide, c3 is 8 bits wide.  The intent of this
        # code is to process the 40 bits in units of 5 bits.  So we take the 1
        # leftover bit of c1 and tack it onto c2.  Then we take the 2 leftover
        # bits of c2 and tack them onto c3.  The shifts and masks are intended
        # to give us values of exactly 5 bits in width.
        c1, c2, c3 = struct.unpack('!HHB', s[i*5:(i+1)*5])
        c2 += (c1 & 1) << 16 # 17 bits wide
        c3 += (c2 & 3) << 8  # 10 bits wide
        parts.extend([_b32tab[c1 >> 11],         # bits 1 - 5
                      _b32tab[(c1 >> 6) & 0x1f], # bits 6 - 10
                      _b32tab[(c1 >> 1) & 0x1f], # bits 11 - 15
                      _b32tab[c2 >> 12],         # bits 16 - 20 (1 - 5)
                      _b32tab[(c2 >> 7) & 0x1f], # bits 21 - 25 (6 - 10)
                      _b32tab[(c2 >> 2) & 0x1f], # bits 26 - 30 (11 - 15)
                      _b32tab[c3 >> 5],          # bits 31 - 35 (1 - 5)
                      _b32tab[c3 & 0x1f],        # bits 36 - 40 (1 - 5)
                      ])
    encoded = EMPTYSTRING.join(parts)
    # Adjust for any leftover partial quanta
    if leftover == 1:
        return encoded[:-6] + '======'
    elif leftover == 2:
        return encoded[:-4] + '===='
    elif leftover == 3:
        return encoded[:-3] + '==='
    elif leftover == 4:
        return encoded[:-1] + '='
    return encoded