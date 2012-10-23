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

from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _

from powerdns_manager import settings


"""
http://doc.powerdns.com/generic-mypgsql-backends.html#idp9002432
http://wiki.powerdns.com/trac/wiki/fields
"""


class Domain(models.Model):
    """Model for PowerDNS domain."""
    
    DOMAIN_TYPE_CHOICES = (
        ('MASTER', 'Master'),
        ('NATIVE', 'Native'),
        ('SLAVE', 'Slave'),
        #('SUPERSLAVE', 'Superslave'),
    )
    name = models.CharField(max_length=255, unique=True, db_index=True, verbose_name=_('name'), help_text="""This field is the actual domainname. This is the field that powerDNS matches to when it gets a request. The domainname should be in the format of: domainname.TLD (no trailing dot)""")
    master = models.CharField(max_length=128, blank=True, null=True, verbose_name=_('master'), help_text="""Enter a comma delimited list of nameservers that are master for this domain. This setting applies only to slave zones.""")
    last_check = models.PositiveIntegerField(max_length=11, blank=True, null=True, verbose_name=_('last check'), help_text="""Last time this domain was checked for freshness.""")
    type = models.CharField(max_length=6, choices=DOMAIN_TYPE_CHOICES, default=settings.PDNS_DEFAULT_ZONE_TYPE, verbose_name=_('type'), help_text="""Select the zone type. Native refers to native SQL replication. Master/Slave refers to DNS server based zone transfers.""")
    notified_serial = models.PositiveIntegerField(max_length=11, blank=True, null=True, verbose_name=_('notified serial'), help_text="""The last notified serial of a master domain. This is updated from the SOA record of the domain.""")
    account = models.CharField(max_length=40, blank=True, null=True, verbose_name=_('account'), help_text="""Determine if a certain host is a supermaster for a certain domain name. (???)""")

    # PowerDNS Manager internal fields
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created on'))
    date_modified = models.DateTimeField(auto_now=True, verbose_name=_('Last Modified'))
    created_by = models.ForeignKey('auth.User', related_name='%(app_label)s_%(class)s_created_by', verbose_name=_('created by'), help_text="""The Django user this zone belongs to.""")
    
    class Meta:
        db_table = 'domains'
        verbose_name = _('domain')
        verbose_name_plural = _('domains')
        get_latest_by = 'date_modified'
        ordering = ['name']

    def __unicode__(self):
        return self.name

#name convert to lowercase



class Record(models.Model):
    """Model for PowerDNS resource record.
    
    Supported record types:
    
        http://doc.powerdns.com/types.html
    
    Rules for filling in AUTH and ORDERNAME fields:
        
        http://doc.powerdns.com/dnssec-modes.html#dnssec-direct-database
    
    
    """
    RECORD_TYPE_CHOICES = (
        ('A', 'A'),
        ('AAAA', 'AAAA'),
        ('AFSDB', 'AFSDB'),
        ('CERT', 'CERT'),
        ('CNAME', 'CNAME'),
        ('DNSKEY', 'DNSKEY'),
        ('DS', 'DS'),
        ('HINFO', 'HINFO'),
        ('KEY', 'KEY'),
        ('LOC', 'LOC'),
        ('MX', 'MX'),
        ('NAPTR', 'NAPTR'),
        ('NS', 'NS'),
        ('NSEC', 'NSEC'),
        ('PTR', 'PTR'),
        ('RP', 'RP'),
        ('RRSIG', 'RRSIG'),
        ('SOA', 'SOA'),
        ('SPF', 'SPF'),
        ('SSHFP', 'SSHFP'),
        ('SRV', 'SRV'),
        ('TXT', 'TXT'),
    )
    domain = models.ForeignKey('powerdns_manager.Domain', related_name='%(app_label)s_%(class)s_domain', verbose_name=_('domain'), help_text=_("""Select the domain this record belongs to."""))
    name = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name=_('name'), help_text="""Actual name of a record. Must not end in a '.' and be fully qualified - it is not relative to the name of the domain!  For example: www.test.com (no trailing dot)""")
    # TODO: Why type allows NULL?
    type = models.CharField(max_length=10, blank=True, null=True, db_index=True, choices=RECORD_TYPE_CHOICES, verbose_name=_('type'), help_text="""Select the record type.""")
    content = models.CharField(max_length=64000, blank=True, null=True, verbose_name=_('content'), help_text="""This is the 'right hand side' of a DNS record. For an A record, this is the IP address for example.""")
    ttl = models.PositiveIntegerField(max_length=11, blank=True, null=True, default=settings.PDNS_DEFAULT_RR_TTL, verbose_name=_('TTL'), help_text="""How long the DNS-client are allowed to remember this record. Also known as Time To Live(TTL) This value is in seconds.""")
    prio = models.PositiveIntegerField(max_length=11, blank=True, null=True, verbose_name=_('priority'), help_text="""For MX records, this should be the priority of the mail exchanger specified.""")
    # Extra fields for DNSSEC (http://doc.powerdns.com/dnssec-modes.html#dnssec-direct-database)
    auth = models.NullBooleanField(verbose_name=_('authoritative'), help_text="""The 'auth' field should be set to '1' for data for which the zone itself is authoritative, which includes the SOA record and its own NS records. The 'auth' field should be 0 however for NS records which are used for delegation, and also for any glue (A, AAAA) records present for this purpose. Do note that the DS record for a secure delegation should be authoritative!""")
    ordername = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name=_('ordername'), help_text="""http://doc.powerdns.com/dnssec-modes.html#dnssec-direct-database""")
    # This should be set on every save  manually
    change_date = models.PositiveIntegerField(max_length=11, blank=True, null=True, verbose_name=_('change date'), help_text="""Timestamp for the last update. This is used by PowerDNS internally.""")

    # PowerDNS Manager internal fields
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created on'))
    date_modified = models.DateTimeField(auto_now=True, verbose_name=_('Last Modified'))

    class Meta:
        db_table = 'records'
        verbose_name = _('record')
        verbose_name_plural = _('records')
        get_latest_by = 'date_modified'
        ordering = ['type']
        order_with_respect_to = 'domain'
        # TODO: Missing: CREATE INDEX nametype_index ON records(name,type);
        # SEE: http://stackoverflow.com/questions/1578195/django-create-index-non-unique-multiple-column
        
    def __unicode__(self):
        return self.name

#name convert to lowercase
# change_date This should be set on every save  manually
# should be set automatically on every save



class SuperMaster(models.Model):
    """Model for PowerDNS supermasters.
    
    More on supermasters: http://doc.powerdns.com/slave.html#supermaster
    
    PDNS can recognize so called 'supermasters'. A supermaster is a host which
    is master for domains and for which we are to be a slave. When a master
    (re)loads a domain, it sends out a notification to its slaves. Normally,
    such a notification is only accepted if PDNS already knows that it is a
    slave for a domain.
    
    SuperMaster records should be added on the secondary DNS servers (slaves).
    This table contains known and trusted master servers.
    
    A supermaster is a host which is master for domains and for which we are to be a slave.  ref  ref2
    This table is an authorization table for the IP/nameserver. 

    """
    ip = models.GenericIPAddressField(verbose_name=_('IP address'), help_text="""IP address for supermaster (IPv4 or IPv6).""")
    # TODO: added unique - check
    nameserver = models.CharField(max_length=255, unique=True, verbose_name=_('nameserver'), help_text="""Hostname of the supermaster.""")
    account = models.CharField(max_length=40, blank=True, null=True, verbose_name=_('account'), help_text="""Account name (???)""")

    # PowerDNS Manager internal fields
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created on'))
    date_modified = models.DateTimeField(auto_now=True, verbose_name=_('Last Modified'))

    class Meta:
        db_table = 'supermasters'
        verbose_name = _('supermaster')
        verbose_name_plural = _('supermasters')
        get_latest_by = 'date_modified'
        ordering = ['nameserver']
        unique_together = (
            ('ip', 'nameserver'),
            #('nameserver', 'account'),    # TODO: check what account really is
        )

    def __unicode__(self):
        return self.nameserver


class DomainMetadata(models.Model):
    """Model for PowerDNS domain metadata.
    
    More on domain metadata: http://doc.powerdns.com/domainmetadata.html
    
    """
    PER_ZONE_METADATA_CHOICES = (
        ('ALLOW-AXFR-FROM', 'ALLOW-AXFR-FROM'),
        ('AXFR-MASTER-TSIG', 'AXFR-MASTER-TSIG'),
        ('LUA-AXFR-SCRIPT', 'LUA-AXFR-SCRIPT'),
        ('NSEC3NARROW', 'NSEC3NARROW'),
        ('NSEC3PARAM', 'NSEC3PARAM'),
        ('PRESIGNED', 'PRESIGNED'),
        ('SOA-EDIT', 'SOA-EDIT'),
        ('TSIG-ALLOW-AXFR', 'TSIG-ALLOW-AXFR'),
    )
    domain = models.ForeignKey('powerdns_manager.Domain', related_name='%(app_label)s_%(class)s_domain', verbose_name=_('domain'), help_text=_("""Select the domain this record belongs to."""))
    kind = models.CharField(max_length=16, choices=PER_ZONE_METADATA_CHOICES, verbose_name=_('setting'), help_text="""Select a setting.""")
    content = models.TextField(blank=True, null=True, verbose_name=_('content'), help_text="""Enter the metadata.""")
    
    # PowerDNS Manager internal fields
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created on'))
    date_modified = models.DateTimeField(auto_now=True, verbose_name=_('Last Modified'))

    class Meta:
        db_table = 'domainmetadata'
        verbose_name = _('domain metadata')
        verbose_name_plural = _('domain metadata')
        get_latest_by = 'date_modified'
        ordering = ['kind']
        order_with_respect_to = 'domain'
        unique_together = (
            ('domain', 'kind'), # TODO: check this
        )
        
    def __unicode__(self):
        return self.kind



class CryptoKey(models.Model):
    """Model for PowerDNS domain crypto keys.
    
    See: http://doc.powerdns.com/dnssec-supported.html
    
    """
    domain = models.ForeignKey('powerdns_manager.Domain', related_name='%(app_label)s_%(class)s_domain', verbose_name=_('domain'), help_text=_("""Select the domain this record belongs to."""))
    flags = models.PositiveIntegerField(verbose_name=_('flags'), help_text="""Key flags.""")
    active = models.BooleanField(verbose_name=_('active'), help_text="""Check to activate key.""")
    # TODO: Check if content may be empty
    content = models.TextField(blank=True, null=True, verbose_name=_('content'), help_text="""Enter the key data.""")
    
    # PowerDNS Manager internal fields
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created on'))
    date_modified = models.DateTimeField(auto_now=True, verbose_name=_('Last Modified'))

    class Meta:
        db_table = 'cryptokeys'
        verbose_name = _('crypto key')
        verbose_name_plural = _('crypto keys')
        get_latest_by = 'date_modified'
        ordering = ['domain']
        unique_together = (
            ('domain', 'flags'), # TODO: check this
        )
        
    def __unicode__(self):
        return self.domain.name



class TsigKey(models.Model):
    """Model for PowerDNS domain TSIG keys.
    
    See: http://doc.powerdns.com/tsig.html
    
    """
    ALGORITHM_CHOICES = (
        ('hmac-md5', 'hmac-md5'),
        # TODO: check for more
    )
    name = models.CharField(max_length=255, verbose_name=_('name'), help_text="""Enter a name for the key.""")
    algorithm = models.CharField(max_length=50, choices=ALGORITHM_CHOICES, verbose_name=_('algorithm'), help_text="""Select hashing algorithm.""")
    secret = models.CharField(max_length=255, verbose_name=_('secret'), help_text="""Enter the shared secret.""")

    # PowerDNS Manager internal fields
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created on'))
    date_modified = models.DateTimeField(auto_now=True, verbose_name=_('Last Modified'))
    created_by = models.ForeignKey('auth.User', related_name='%(app_label)s_%(class)s_created_by', verbose_name=_('created by'), help_text="""The Django user this TSIG key belongs to.""")


    class Meta:
        db_table = 'tsigkeys'
        verbose_name = _('TSIG Key')
        verbose_name_plural = _('TSIG Keys')
        get_latest_by = 'date_modified'
        ordering = ['name']
        unique_together = (
            ('name', 'algorithm'),
        )
        
    def __unicode__(self):
        return self.name


