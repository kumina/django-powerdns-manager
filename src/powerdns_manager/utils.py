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

