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
from powerdns_manager.forms import GenericRecordModelForm

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


class GenericRecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    form = GenericRecordModelForm
    fields = ('name', 'type_avail', 'ttl', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    extra = 0
    verbose_name = 'Other Resource Record'
    verbose_name_plural = 'Other Resource Records'
    
    def queryset(self, request):
        """Exclude resource records which are editable in a separate Inline"""
        qs = super(GenericRecordInline, self).queryset(request)
        qs = qs.exclude(type='SOA')
        qs = qs.exclude(type='NS')
        qs = qs.exclude(type='MX')
        qs = qs.exclude(type='SRV')
        return qs


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
        SoaRecordInline,
        NsRecordInline,
        MxRecordInline,
        SrvRecordInline,
        GenericRecordInline,
        DomainMetadataInline,
        CryptoKeyInline
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

