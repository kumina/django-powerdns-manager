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

from django.db.models.loading import cache

from powerdns_manager import settings



def set_soa_rr_name(sender, **kwargs):
    """Sets the ``name`` field of the SOA record.
    
    PowerDNS Manager allows only one SOA RR per zone.
    
    This callback updates the ``name`` field of the SOA record and
    sats it eual to the name of the associated domain.
    
    """
    instance = kwargs['instance']   # powerdns_manager.Record instance
    if instance.type == 'SOA':
        instance.name = instance.domain.name


def update_rr_change_date(sender, **kwargs):
    """Sets the current timestamp to the ``change_date`` field.
    
    This is used by PowerDNS.
    
    """
    instance = kwargs['instance']   # powerdns_manager.Record instance
    instance.change_date = int(time.time())


def set_rr_ttl(sender, **kwargs):
    """Sets the TTL of the resource record(s).
    
    This is done according to the following rules:
    
    1) TTL of SOA RRs is not modified. The TTL field is mandatory on SOA
    records (see forms.SoaRecordModelForm) and also defines the minimum TTL
    get_minimum_ttl() retrieves.
    
    2) If the RR is not a SOA and if TTL is missing, the minimum TTL of
    the zone (as defined in the SOA record) will be used. If a SOA record
    is missing, PDNS_DEFAULT_RR_TTL is returned by Domain.get.minimum_ttl().
    
    """
    instance = kwargs['instance']   # powerdns_manager.Record instance
    if not instance.ttl and instance.type != 'SOA':
        instance.ttl = instance.domain.get_minimum_ttl()


def set_rr_authoritative(sender, **kwargs):
    """This callback fills the ``auth`` field of the Record model.
    
    TODO: list the rules to fill the field.
    
    """ 
    instance = kwargs['instance']   # powerdns_manager.Record instance


def set_rr_ordername(sender, **kwargs):
    """This callback fills the ``ordername`` field of the Record model.
    
    TODO: list the rules to fill the field.
    
    """ 
    instance = kwargs['instance']   # powerdns_manager.Record instance


