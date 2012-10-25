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



def update_rr_change_date(sender, **kwargs):
    instance = kwargs['instance']   # powerdns_manager.Record instance
    instance.change_date = int(time.time())


def set_missing_ttl(sender, **kwargs):
    instance = kwargs['instance']   # powerdns_manager.Record instance
    instance.ttl = settings.PDNS_DEFAULT_RR_TTL
    # TODO: consider checking the minimum TTL from the SOA record.


def set_rr_authoritative_field(sender, **kwargs):
    """This callback fills the ``auth`` field of the Record model.
    
    TODO: list the rules to fill the field.
    
    """ 
    instance = kwargs['instance']   # powerdns_manager.Record instance


def set_rr_ordername_field(sender, **kwargs):
    """This callback fills the ``ordername`` field of the Record model.
    
    TODO: list the rules to fill the field.
    
    """ 
    instance = kwargs['instance']   # powerdns_manager.Record instance


