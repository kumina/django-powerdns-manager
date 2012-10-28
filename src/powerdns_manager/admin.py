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

from django.contrib import admin
from django.db.models.loading import cache
from django.contrib import messages
from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _


from powerdns_manager import settings

from powerdns_manager.forms import SoaRecordModelForm
from powerdns_manager.forms import NsRecordModelForm
from powerdns_manager.forms import MxRecordModelForm
from powerdns_manager.forms import SrvRecordModelForm
from powerdns_manager.forms import ARecordModelForm
from powerdns_manager.forms import AaaaRecordModelForm
from powerdns_manager.forms import CnameRecordModelForm
from powerdns_manager.forms import PtrRecordModelForm
from powerdns_manager.forms import TxtRecordModelForm
from powerdns_manager.forms import DsRecordModelForm
from powerdns_manager.forms import CertRecordModelForm
from powerdns_manager.forms import HinfoRecordModelForm
from powerdns_manager.forms import LocRecordModelForm
from powerdns_manager.forms import SpfRecordModelForm
from powerdns_manager.forms import SshfpRecordModelForm
from powerdns_manager.forms import RpRecordModelForm
from powerdns_manager.forms import NaptrRecordModelForm
from powerdns_manager.forms import AfsdbRecordModelForm
from powerdns_manager.forms import DnskeyRecordModelForm
from powerdns_manager.forms import KeyRecordModelForm
from powerdns_manager.forms import NsecRecordModelForm
from powerdns_manager.forms import RrsigRecordModelForm

# Action for
# - set change date
# - set serial (?)
# - set TTL to 300, 3600, 86400
#
#def test_action(modeladmin, request, queryset):
#    messages.add_message(request, messages.INFO, 'The test action was successful.')
#test_action.short_description = "Test Action"


class BaseTabularRecordInline(admin.TabularInline):
    RR_TYPE = '__OVERRIDE__'
    form = '__OVERRIDE__'
    model = cache.get_model('powerdns_manager', 'Record')
    extra = 0
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def __init__(self, *args, **kwargs):
        self.verbose_name = '%s Resource Record' % self.RR_TYPE
        self.verbose_name_plural = '%s Resource Records' % self.RR_TYPE
        super(BaseTabularRecordInline, self).__init__(*args, **kwargs)
        
    def queryset(self, request):
        """Return only RR_TYPE records"""
        qs = super(BaseTabularRecordInline, self).queryset(request)
        return qs.filter(type=self.RR_TYPE)



class SoaRecordInline(admin.StackedInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = SoaRecordModelForm
    # Show exactly one form
    extra = 1
    max_num = 1
    verbose_name = 'SOA Resource Record'
    verbose_name_plural = 'SOA Resource Record' # Only one SOA RR per zone
    # The ``name`` field is not available for editing. It is always set to the
    # name of the domain in ``signal_cb.theset_soa_rr_name()`` callback.
    fields = ('ttl', 'primary', 'hostmaster', 'serial', 'refresh', 'retry', 'expire', 'default_ttl', 'date_modified')
    readonly_fields = ('date_modified', )
    can_delete = False
    
    def queryset(self, request):
        """Return only SOA records"""
        qs = super(SoaRecordInline, self).queryset(request)
        return qs.filter(type='SOA')


class NsRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'NS'
    form = NsRecordModelForm

class MxRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'MX'
    form = MxRecordModelForm
    fields = ('name', 'ttl', 'prio', 'content', 'date_modified')
    
class SrvRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'SRV'
    form = SrvRecordModelForm
    fields = ('name', 'ttl', 'prio', 'content', 'date_modified')

class ARecordInline(BaseTabularRecordInline):
    RR_TYPE = 'A'
    form = ARecordModelForm

class AaaaRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'AAAA'
    form = AaaaRecordModelForm

class CnameRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'CNAME'
    form = CnameRecordModelForm

class PtrRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'PTR'
    form = PtrRecordModelForm

class TxtRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'TXT'
    form = TxtRecordModelForm

class DsRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'DS'
    form = DsRecordModelForm

class CertRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'CERT'
    form = CertRecordModelForm

class HinfoRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'HINFO'
    form = HinfoRecordModelForm

class LocRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'LOC'
    form = LocRecordModelForm

class SpfRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'SPF'
    form = SpfRecordModelForm

class SshfpRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'SSHFP'
    form = SshfpRecordModelForm

class RpRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'RP'
    form = RpRecordModelForm

class NaptrRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'NAPTR'
    form = NaptrRecordModelForm

class AfsdbRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'AFSDB'
    form = AfsdbRecordModelForm

class DnskeyRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'DNSKEY'
    form = DnskeyRecordModelForm

class KeyRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'KEY'
    form = KeyRecordModelForm

class NsecRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'NSEC'
    form = NsecRecordModelForm

class RrsigRecordInline(BaseTabularRecordInline):
    RR_TYPE = 'RRSIG'
    form = RrsigRecordModelForm


class DomainMetadataInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'DomainMetadata')
    fields = ('kind', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    extra = 0
    verbose_name_plural = 'Domain Metadata'

    
class CryptoKeyInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'CryptoKey')
    fields = ('flags', 'active', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    extra = 0
    verbose_name_plural = 'Crypto Keys'




class DomainAdmin(admin.ModelAdmin):
    #form = DomainModelForm
    #actions = [test_action, ]
    
    fields = ('name', 'type', 'master', 'date_modified')
    readonly_fields = ('date_modified', )
    list_display = ('name', 'type', 'master', 'date_modified')
    list_filter = ('type', )
    search_fields = ('name', 'master')
    verbose_name = 'zone'
    verbose_name_plural = 'zones'
    save_on_top = True
    
    #
    # Build the ``inlines`` list. Only inlines for enabled RR types are included.
    # 
    inlines = []
    
    # Resource Record type to Resource Record Inline Map
    RR_INLINE_MAP = {
        'A':        ARecordInline,
        'AAAA':     AaaaRecordInline,
        'AFSDB':    AfsdbRecordInline,
        'CERT':     CertRecordInline,
        'CNAME':    CnameRecordInline,
        'DNSKEY':   DnskeyRecordInline,
        'DS':       DsRecordInline,
        'HINFO':    HinfoRecordInline,
        'KEY':      KeyRecordInline,
        'LOC':      LocRecordInline,
        'MX':       MxRecordInline,
        'NAPTR':    NaptrRecordInline,
        'NS':       NsRecordInline,
        'NSEC':     NsecRecordInline,
        'PTR':      PtrRecordInline,
        'RP':       RpRecordInline,
        'RRSIG':    RrsigRecordInline,
        'SOA':      SoaRecordInline,
        'SPF':      SpfRecordInline,
        'SSHFP':    SshfpRecordInline,
        'SRV':      SrvRecordInline,
        'TXT':      TxtRecordInline,
    }
    
    # Add RR inlines
    for RR_TYPE in settings.PDNS_ENABLED_RR_TYPES:
        inlines.append(RR_INLINE_MAP[RR_TYPE])
    
    # Add other inlines
    inlines.append(DomainMetadataInline)
    inlines.append(CryptoKeyInline)
    
    def queryset(self, request):
        qs = super(DomainAdmin, self).queryset(request)
        if not request.user.is_superuser:
            # Non-superusers see the domains they have created
            qs = qs.filter(created_by=request.user)
        return qs
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.save()
    
admin.site.register(cache.get_model('powerdns_manager', 'Domain'), DomainAdmin)



class TsigKeyAdmin(admin.ModelAdmin):
    fields = ('name', 'algorithm', 'secret', 'date_modified')
    readonly_fields = ('date_modified', )
    list_display = ('name', 'algorithm', 'date_modified')
    list_filter = ('algorithm', )
    search_fields = ('name', )
    verbose_name = 'TSIG Key'
    verbose_name_plural = 'TSIG Keys'
    
    def queryset(self, request):
        qs = super(TsigKeyAdmin, self).queryset(request)
        if not request.user.is_superuser:
            # Non-superusers see the records they have created
            qs = qs.filter(created_by=request.user)
        return qs
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.save()
    
admin.site.register(cache.get_model('powerdns_manager', 'TsigKey'), TsigKeyAdmin)



class SuperMasterAdmin(admin.ModelAdmin):
    fields = ('ip', 'nameserver', 'account', 'date_modified')
    readonly_fields = ('date_modified', )
    list_display = ('ip', 'nameserver', 'account', 'date_modified')
    search_fields = ('nameserver', 'account')
    verbose_name = 'SuperMaster'
    verbose_name_plural = 'SuperMasters'
    
admin.site.register(cache.get_model('powerdns_manager', 'SuperMaster'), SuperMasterAdmin)

