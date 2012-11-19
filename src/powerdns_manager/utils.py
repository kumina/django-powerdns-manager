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
import hashlib
import base64
import string
import StringIO

import dns.zone
import dns.query
from dns.zone import BadZone, NoSOA, NoNS, UnknownOrigin
from dns.exception import DNSException
import dns.rdataclass
import dns.rdatatype
import dns.rdtypes
import dns.rdtypes.ANY
from dns.rdtypes.ANY import *
import dns.rdtypes.IN
from dns.rdtypes.IN import *
from dns.name import Name

from django.db.models.loading import cache



def generate_serial(old_serial=None, is_timestamp=True):
    """Generates a new serial for the zone.
    
    Currently returns the Unix timestamp.
    
    """
    return int(time.time()) 


def process_zone_file(origin, zonetext, overwrite=False):
    """Imports zone to the database.
    
    No checks for existence are performed in this file. For form processing,
    see the ``import_zone_view`` view.
    

    
    """
    if origin:
        origin = Name((origin.rstrip('.') + '.').split('.'))
    else:
        origin = None
    
    zonetext = str(zonetext)
    zonetext = zonetext.replace('\r\n', '\n')
    
    try:
        zone = dns.zone.from_text(zonetext, origin=origin, relativize=False)
        if not str(zone.origin).rstrip('.'):
            raise UnknownOrigin
        
        process_and_import_zone_data(zone, overwrite)
        
    except NoSOA:
        raise Exception('The zone has no SOA RR at its origin')
    except NoNS:
        raise Exception('The zone has no NS RRset at its origin')
    except UnknownOrigin:
        raise Exception('The zone\'s origin is unknown')
    except BadZone:
        raise Exception('The zone is malformed')
    except DNSException, e:
        #raise Exception(str(e))
        raise Exception('The zone is malformed')


def process_axfr_response(origin, nameserver, overwrite=False):
    """
    origin: string domain name
    nameserver: IP of the DNS server
    
    """
    origin = Name((origin.rstrip('.') + '.').split('.'))
    axfr_query = dns.query.xfr(nameserver, origin, timeout=5, relativize=False, lifetime=10)
    
    try:
        zone = dns.zone.from_xfr(axfr_query, relativize=False)
        if not str(zone.origin).rstrip('.'):
            raise UnknownOrigin
        
        process_and_import_zone_data(zone, overwrite)
        
    except NoSOA:
        raise Exception('The zone has no SOA RR at its origin')
    except NoNS:
        raise Exception('The zone has no NS RRset at its origin')
    except UnknownOrigin:
        raise Exception('The zone\'s origin is unknown')
    except BadZone:
        raise Exception('The zone is malformed')
    except DNSException, e:
        #raise Exception(str(e))
        raise Exception('The zone is malformed')
    

def process_and_import_zone_data(zone, overwrite=False):
    """
    zone: dns.zone
    
    *****
    Special kudos to Grig Gheorghiu for demonstrating how to manage zone files
    using dnspython in the following article:
    http://agiletesting.blogspot.com/2005/08/managing-dns-zone-files-with-dnspython.html
    *****
    
    """
    Domain = cache.get_model('powerdns_manager', 'Domain')
    Record = cache.get_model('powerdns_manager', 'Record')
    
    # Check if zone already exists in the database.
    try:
        domain_instance = Domain.objects.get(name=str(zone.origin).rstrip('.'))
    except Domain.DoesNotExist:
        pass    # proceed with importing the new zone data
    else:   # Zone exists
        if overwrite:
            # If ``overwrite`` has been checked, then delete the current zone.
            domain_instance.delete()
        else:
            raise Exception('Zone already exists. Consider using the "overwrite" option')
    
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
                
                if rdataset.rdtype == dns.rdatatype._by_text['SOA']:
                    # Set type
                    rr.type = 'SOA'
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

                elif rdataset.rdtype == dns.rdatatype._by_text['NS']:
                    # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.ANY.NS.NS-class.html
                    rr.type = 'NS'
                    rr.content = str(rdata.target).rstrip('.')

                elif rdataset.rdtype == dns.rdatatype._by_text['MX']:
                    # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.ANY.MX.MX-class.html
                    rr.type = 'MX'
                    rr.content = str(rdata.exchange).rstrip('.')
                    rr.prio = rdata.preference
                
                elif rdataset.rdtype == dns.rdatatype._by_text['TXT']:
                    # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.ANY.TXT.TXT-class.html
                    rr.type = 'TXT'
                    rr.content = ' '.join(rdata.strings)
                
                elif rdataset.rdtype == dns.rdatatype._by_text['CNAME']:
                    # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.ANY.CNAME.CNAME-class.html
                    rr.type = 'CNAME'
                    rr.content = str(rdata.target).rstrip('.')
                    
                elif rdataset.rdtype == dns.rdatatype._by_text['A']:
                    # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.IN.A.A-class.html
                    rr.type = 'A'
                    rr.content = rdata.address
                
                elif rdataset.rdtype == dns.rdatatype._by_text['AAAA']:
                    # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.IN.AAAA.AAAA-class.html
                    rr.type = 'AAAA'
                    rr.content = rdata.address
                
                elif rdataset.rdtype == dns.rdatatype._by_text['SPF']:
                    # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.ANY.SPF.SPF-class.html
                    rr.type = 'SPF'
                    rr.content = ' '.join(rdata.strings)
                
                elif rdataset.rdtype == dns.rdatatype._by_text['PTR']:
                    # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.ANY.PTR.PTR-class.html
                    rr.type = 'PTR'
                    rr.content = str(rdata.target).rstrip('.')
                
                elif rdataset.rdtype == dns.rdatatype._by_text['SRV']:
                    # http://www.dnspython.org/docs/1.10.0/html/dns.rdtypes.IN.SRV.SRV-class.html
                    rr.type = 'SRV'
                    rr.content = '%d %d %s' % (rdata.weight, rdata.port, str(rdata.target).rstrip('.'))
                
                rr.save()
    
    # Update zone serial
    the_domain.update_serial()
    
    # Rectify zone
    rectify_zone(the_domain.name)



def generate_zone_file(origin):
    """Generates a zone file.
    
    Accepts the zone origin as string (no trailing dot).
     
    Returns the contents of a zone file that contains all the resource records
    associated with the domain with the provided origin.
    
    """
    Domain = cache.get_model('powerdns_manager', 'Domain')
    Record = cache.get_model('powerdns_manager', 'Record')
    
    the_domain = Domain.objects.get(name__exact=origin)
    the_rrs = Record.objects.filter(domain=the_domain).order_by('-type')
    
    # Generate the zone file
    
    origin = Name((origin.rstrip('.') + '.').split('.'))
    
    # Create an empty dns.zone object.
    # We set check_origin=False because the zone contains no records.
    zone = dns.zone.from_text('', origin=origin, relativize=False, check_origin=False)
    
    rdclass = dns.rdataclass._by_text.get('IN')
    
    for rr in the_rrs:
        
        # Add trailing dot to rr.name
        record_name = rr.name.rstrip('.') + '.'
        
        if rr.type == 'SOA':
            # Add SOA Resource Record
            
            # SOA content:  primary hostmaster serial refresh retry expire default_ttl
            bits = rr.content.split()
            # Primary nameserver of SOA record
            primary = bits[0].rstrip('.') + '.'
            mname = Name(primary.split('.'))
            # Responsible hostmaster from SOA record
            hostmaster = bits[1].rstrip('.') + '.'
            rname = Name(hostmaster.split('.'))
            
            rdtype = dns.rdatatype._by_text.get('SOA')
            rdataset = zone.find_rdataset(record_name, rdtype=rdtype, create=True)
            rdata = dns.rdtypes.ANY.SOA.SOA(rdclass, rdtype,
                mname = mname,
                rname = rname,
                serial = int(bits[2]),
                refresh = int(bits[3]),
                retry = int(bits[4]),
                expire = int(bits[5]),
                minimum = int(bits[6])
            )
            rdataset.add(rdata, ttl=int(rr.ttl))
        
        elif rr.type == 'NS':
            # Add NS Resource Record
            rdtype = dns.rdatatype._by_text.get('NS')
            rdataset = zone.find_rdataset(record_name, rdtype=rdtype, create=True)
            rdata = dns.rdtypes.ANY.NS.NS(rdclass, rdtype,
                target = Name((rr.content.rstrip('.') + '.').split('.'))
            )
            rdataset.add(rdata, ttl=int(rr.ttl))
        
        elif rr.type == 'MX':
            # Add MX Resource Record
            rdtype = dns.rdatatype._by_text.get('MX')
            rdataset = zone.find_rdataset(record_name, rdtype=rdtype, create=True)
            rdata = dns.rdtypes.ANY.MX.MX(rdclass, rdtype,
                preference = int(rr.prio),
                exchange = Name((rr.content.rstrip('.') + '.').split('.'))
            )
            rdataset.add(rdata, ttl=int(rr.ttl))
        
        elif rr.type == 'TXT':
            # Add TXT Resource Record
            rdtype = dns.rdatatype._by_text.get('TXT')
            rdataset = zone.find_rdataset(record_name, rdtype=rdtype, create=True)
            rdata = dns.rdtypes.ANY.TXT.TXT(rdclass, rdtype,
                strings = rr.content.split()
            )
            rdataset.add(rdata, ttl=int(rr.ttl))
        
        elif rr.type == 'CNAME':
            # Add CNAME Resource Record
            rdtype = dns.rdatatype._by_text.get('CNAME')
            rdataset = zone.find_rdataset(record_name, rdtype=rdtype, create=True)
            rdata = dns.rdtypes.ANY.CNAME.CNAME(rdclass, rdtype,
                target = Name((rr.content.rstrip('.') + '.').split('.'))
            )
            rdataset.add(rdata, ttl=int(rr.ttl))
        
        elif rr.type == 'A':
            # Add A Resource Record
            rdtype = dns.rdatatype._by_text.get('A')
            rdataset = zone.find_rdataset(record_name, rdtype=rdtype, create=True)
            rdata = dns.rdtypes.IN.A.A(rdclass, rdtype,
                address = rr.content
            )
            rdataset.add(rdata, ttl=int(rr.ttl))
        
        elif rr.type == 'AAAA':
            # Add AAAA Resource Record
            rdtype = dns.rdatatype._by_text.get('AAAA')
            rdataset = zone.find_rdataset(record_name, rdtype=rdtype, create=True)
            rdata = dns.rdtypes.IN.AAAA.AAAA(rdclass, rdtype,
                address = rr.content
            )
            rdataset.add(rdata, ttl=int(rr.ttl))
        
        elif rr.type == 'SPF':
            # Add SPF Resource Record
            rdtype = dns.rdatatype._by_text.get('SPF')
            rdataset = zone.find_rdataset(record_name, rdtype=rdtype, create=True)
            rdata = dns.rdtypes.ANY.SPF.SPF(rdclass, rdtype,
                strings = rr.content.split()
            )
            rdataset.add(rdata, ttl=int(rr.ttl))
        
        elif rr.type == 'PTR':
            # Add PTR Resource Record
            rdtype = dns.rdatatype._by_text.get('PTR')
            rdataset = zone.find_rdataset(record_name, rdtype=rdtype, create=True)
            rdata = dns.rdtypes.ANY.PTR.PTR(rdclass, rdtype,
                target = Name((rr.content.rstrip('.') + '.').split('.'))
            )
            rdataset.add(rdata, ttl=int(rr.ttl))
        
        elif rr.type == 'SRV':
            # Add SRV Resource Record
            
            # weight port target
            weight, port, target = rr.content.split()
            
            rdtype = dns.rdatatype._by_text.get('SRV')
            rdataset = zone.find_rdataset(record_name, rdtype=rdtype, create=True)
            rdata = dns.rdtypes.IN.SRV.SRV(rdclass, rdtype,
                priority = int(rr.prio),
                weight = int(weight),
                port = int(port),
                target = Name((target.rstrip('.') + '.').split('.'))
            )
            rdataset.add(rdata, ttl=int(rr.ttl))
            
    
    # Export text (from the source code of http://www.dnspython.org/docs/1.10.0/html/dns.zone.Zone-class.html#to_file)
    EOL = '\r\n'
    f = StringIO.StringIO()
    f.write('$ORIGIN %s%s' % (origin, EOL))
    zone.to_file(f, sorted=True, relativize=False, nl=EOL)
    data = f.getvalue()
    f.close()
    return data
    


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
                    rr.ordername = pdnssec_hash_zone_record(rr.domain.name , rr.name)
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




def sha1hash(x, salt):
    s = hashlib.sha1()
    s.update(x)
    s.update(salt)
    return s.digest()



# ``base32hex`` encoding is described in Section 7 of RFC4648
#
#       http://tools.ietf.org/html/rfc4648#section-7
#
# Translation table for normal base32 to base32 with extended hex
# alphabet used by NSEC3 (see RFC 4648, Section 7). This alphabet
# has the property that encoded data maintains its sort order when
# compared bitwise.
b32_to_ext_hex = string.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567',
                                  '0123456789ABCDEFGHIJKLMNOPQRSTUV')

def pdnssec_hash_zone_record(zone_name, record_name):
    """Generates hash for ordername field in NSEC3 non-narrow mode.
    
    *****
    Special kudos to the folks at the #powerdns IRC channel for the help,
    especially Maik for pointing me to dns.name.Name.to_digestable() method.
    *****
    
    Notes from RFCs for easy reference
    ----------------------------------
    
    NSEC3PARAM Presentation Format:
    
        http://tools.ietf.org/html/rfc5155#section-4.3
    
    4.3. Presentation Format
     
    The presentation format of the RDATA portion is as follows:
    
    - The Hash Algorithm field is represented as an unsigned decimal
    integer.  The value has a maximum of 255.
    
    - The Flags field is represented as an unsigned decimal integer.
    The value has a maximum value of 255.
    
    - The Iterations field is represented as an unsigned decimal
    integer.  The value is between 0 and 65535, inclusive.
    
    - The Salt Length field is not represented.
    
    - The Salt field is represented as a sequence of case-insensitive
    hexadecimal digits.  Whitespace is not allowed within the
    sequence.  This field is represented as "-" (without the quotes)
    when the Salt Length field is zero.


    5. Calculation of the Hash
       http://tools.ietf.org/html/rfc5155#section-5
    The hash calculation uses three of the NSEC3 RDATA fields: Hash
    Algorithm, Salt, and Iterations.
    
    Define H(x) to be the hash of x using the Hash Algorithm selected by
    the NSEC3 RR, k to be the number of Iterations, and || to indicate
    concatenation.  Then define:
    
    IH(salt, x, 0) = H(x || salt), and
    
    IH(salt, x, k) = H(IH(salt, x, k-1) || salt), if k > 0
    
    Then the calculated hash of an owner name is
    
    IH(salt, owner name, iterations),
    
    where the owner name is in the canonical form, defined as:
    
    The wire format of the owner name where:
    
    1.  The owner name is fully expanded (no DNS name compression) and
    fully qualified;
    
    2.  All uppercase US-ASCII letters are replaced by the corresponding
    lowercase US-ASCII letters;
    
    3.  If the owner name is a wildcard name, the owner name is in its
    original unexpanded form, including the "*" label (no wildcard
    substitution);
    
    This form is as defined in Section 6.2 of [RFC4034].
    
    The method to calculate the Hash is based on [RFC2898].
    
    "DNSSEC NSEC3 Hash Algorithms".
   The initial contents of this registry are:

      0 is Reserved.

      1 is SHA-1.

      2-255 Available for assignment.
    """
    
    Domain = cache.get_model('powerdns_manager', 'Domain')
    DomainMetadata = cache.get_model('powerdns_manager', 'DomainMetadata')
    
    the_domain = Domain.objects.get(name__exact=zone_name)
    nsec3param = DomainMetadata.objects.get(domain=the_domain, kind='NSEC3PARAM')
    algo, flags, iterations, salt = nsec3param.content.split()
    
    # dns.name.NAME expects an absolute name (with trailing dot)
    record_name = '%s.' % record_name.rstrip('.')
    record_name = Name(record_name.split('.'))
    
    # Prepare salt
    salt = salt.decode('hex')
    
    hashed_name = sha1hash(record_name.to_digestable(), salt)
    i = 0
    while i < int(iterations):
        hashed_name = sha1hash(hashed_name, salt)
        i += 1
    
    # Do standard base32 encoding
    final_data = base64.b32encode(hashed_name)
    # Apply the translation table to convert to base32hex encoding.
    final_data = final_data.translate(b32_to_ext_hex)
    # Return lower case representation as required by PowerDNS
    return final_data.lower()


