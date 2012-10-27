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


class NsRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = NsRecordModelForm
    extra = 0
    verbose_name = 'NS Resource Record'
    verbose_name_plural = 'NS Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only NS records"""
        qs = super(NsRecordInline, self).queryset(request)
        return qs.filter(type='NS')


class MxRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = MxRecordModelForm
    extra = 0
    verbose_name = 'MX Resource Record'
    verbose_name_plural = 'MX Resource Records'
    fields = ('name', 'ttl', 'prio', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only MX records"""
        qs = super(MxRecordInline, self).queryset(request)
        return qs.filter(type='MX')
    

class SrvRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = SrvRecordModelForm
    extra = 0
    verbose_name = 'SRV Resource Record'
    verbose_name_plural = 'SRV Resource Records'
    fields = ('name', 'ttl', 'prio', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only SRV records"""
        qs = super(SrvRecordInline, self).queryset(request)
        return qs.filter(type='SRV')


class ARecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = ARecordModelForm
    extra = 0
    verbose_name = 'A Resource Record'
    verbose_name_plural = 'A Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only A records"""
        qs = super(ARecordInline, self).queryset(request)
        return qs.filter(type='A')


class AaaaRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = AaaaRecordModelForm
    extra = 0
    verbose_name = 'AAAA Resource Record'
    verbose_name_plural = 'AAAA Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only AAAA records"""
        qs = super(AaaaRecordInline, self).queryset(request)
        return qs.filter(type='AAAA')


class CnameRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = CnameRecordModelForm
    extra = 0
    verbose_name = 'CNAME Resource Record'
    verbose_name_plural = 'CNAME Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only CNAME records"""
        qs = super(CnameRecordInline, self).queryset(request)
        return qs.filter(type='CNAME')


class PtrRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = PtrRecordModelForm
    extra = 0
    verbose_name = 'PTR Resource Record'
    verbose_name_plural = 'PTR Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only PTR records"""
        qs = super(PtrRecordInline, self).queryset(request)
        return qs.filter(type='PTR')


class TxtRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = TxtRecordModelForm
    extra = 0
    verbose_name = 'TXT Resource Record'
    verbose_name_plural = 'TXT Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only TXT records"""
        qs = super(TxtRecordInline, self).queryset(request)
        return qs.filter(type='TXT')


class DsRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = DsRecordModelForm
    extra = 0
    verbose_name = 'DS Resource Record'
    verbose_name_plural = 'DS Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only DS records"""
        qs = super(DsRecordInline, self).queryset(request)
        return qs.filter(type='DS')


class CertRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = CertRecordModelForm
    extra = 0
    verbose_name = 'CERT Resource Record'
    verbose_name_plural = 'CERT Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only CERT records"""
        qs = super(CertRecordInline, self).queryset(request)
        return qs.filter(type='CERT')


class HinfoRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = HinfoRecordModelForm
    extra = 0
    verbose_name = 'HINFO Resource Record'
    verbose_name_plural = 'HINFO Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only HINFO records"""
        qs = super(HinfoRecordInline, self).queryset(request)
        return qs.filter(type='HINFO')


class LocRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = LocRecordModelForm
    extra = 0
    verbose_name = 'LOC Resource Record'
    verbose_name_plural = 'LOC Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only LOC records"""
        qs = super(LocRecordInline, self).queryset(request)
        return qs.filter(type='LOC')


class SpfRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = SpfRecordModelForm
    extra = 0
    verbose_name = 'SPF Resource Record'
    verbose_name_plural = 'SPF Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only SPF records"""
        qs = super(SpfRecordInline, self).queryset(request)
        return qs.filter(type='SPF')


class SshfpRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = SshfpRecordModelForm
    extra = 0
    verbose_name = 'SSHFP Resource Record'
    verbose_name_plural = 'SSHFP Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only SSHFP records"""
        qs = super(SshfpRecordInline, self).queryset(request)
        return qs.filter(type='SSHFP')


class RpRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = RpRecordModelForm
    extra = 0
    verbose_name = 'RP Resource Record'
    verbose_name_plural = 'RP Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only RP records"""
        qs = super(RpRecordInline, self).queryset(request)
        return qs.filter(type='RP')


class NaptrRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = NaptrRecordModelForm
    extra = 0
    verbose_name = 'NAPTR Resource Record'
    verbose_name_plural = 'NAPTR Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only NAPTR records"""
        qs = super(NaptrRecordInline, self).queryset(request)
        return qs.filter(type='NAPTR')


class AfsdbRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = AfsdbRecordModelForm
    extra = 0
    verbose_name = 'AFSDB Resource Record'
    verbose_name_plural = 'AFSDB Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only AFSDB records"""
        qs = super(AfsdbRecordInline, self).queryset(request)
        return qs.filter(type='AFSDB')


class DnskeyRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = DnskeyRecordModelForm
    extra = 0
    verbose_name = 'DNSKEY Resource Record'
    verbose_name_plural = 'DNSKEY Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only DNSKEY records"""
        qs = super(DnskeyRecordInline, self).queryset(request)
        return qs.filter(type='DNSKEY')


class KeyRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = KeyRecordModelForm
    extra = 0
    verbose_name = 'KEY Resource Record'
    verbose_name_plural = 'KEY Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only KEY records"""
        qs = super(KeyRecordInline, self).queryset(request)
        return qs.filter(type='KEY')


class NsecRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = NsecRecordModelForm
    extra = 0
    verbose_name = 'NSEC Resource Record'
    verbose_name_plural = 'NSEC Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only NSEC records"""
        qs = super(NsecRecordInline, self).queryset(request)
        return qs.filter(type='NSEC')


class RrsigRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = RrsigRecordModelForm
    extra = 0
    verbose_name = 'RRSIG Resource Record'
    verbose_name_plural = 'RRSIG Resource Records'
    fields = ('name', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    
    def queryset(self, request):
        """Return only RRSIG records"""
        qs = super(RrsigRecordInline, self).queryset(request)
        return qs.filter(type='RRSIG')


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
    inlines = [
        # RR
        SoaRecordInline,
        NsRecordInline,
        MxRecordInline,
        ARecordInline,
        AaaaRecordInline,
        CnameRecordInline,
        PtrRecordInline,
        TxtRecordInline,
        SrvRecordInline,
        DsRecordInline,
        CertRecordInline,
        HinfoRecordInline,
        LocRecordInline,
        SpfRecordInline,
        SshfpRecordInline,
        RpRecordInline,
        NaptrRecordInline,
        AfsdbRecordInline,
        DnskeyRecordInline,
        KeyRecordInline,
        NsecRecordInline,
        RrsigRecordInline,
        # Other
        DomainMetadataInline,
        CryptoKeyInline,
    ]
    verbose_name = 'zone'
    verbose_name_plural = 'zones'
    save_on_top = True
    
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

