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

# Action for
# - set change date
# - set serial (?)
# - set TTL to 300, 3600, 86400
#
#def test_action(modeladmin, request, queryset):
#    messages.add_message(request, messages.INFO, 'The test action was successful.')
#test_action.short_description = "Test Action"


class OwnDomainListFilter(SimpleListFilter):
    title = _('domain')
    parameter_name = 'domain'

    def lookups(self, request, model_admin):
        Domain = cache.get_model('powerdns_manager', 'Domain')
        qs = Domain.objects.filter(created_by=request.user)
        for namespace in qs:
            yield (namespace, namespace)

    def queryset(self, request, queryset):
        the_domain = self.value()
        if the_domain:
            return queryset.filter(domain__name=the_domain, domain__created_by=request.user)
        return queryset


class RecordInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'Record')
    fields = ('name', 'type', 'ttl', 'prio', 'content', 'auth', 'date_modified')
    readonly_fields = ('date_modified', )
    extra = 1

class DomainMetadataInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'DomainMetadata')
    fields = ('kind', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    extra = 0
    
class CryptoKeyInline(admin.TabularInline):
    model = cache.get_model('powerdns_manager', 'CryptoKey')
    fields = ('flags', 'active', 'content', 'date_modified')
    readonly_fields = ('date_modified', )
    extra = 0


class DomainAdmin(admin.ModelAdmin):
    #form = DomainModelForm
    #actions = [reload_php_stack, ]
    
    fieldsets = (
        ('', {
            'fields' : ('name', 'type', 'master'),
            #'description' : 'Main virtual host attributes',
        }),
        ('Info', {
            'classes' : ('collapse',),
            'fields' : ('date_created', 'date_modified', ),
            #'description' : 'Information about the domain.',
        }),
    )
    readonly_fields = ('date_created', 'date_modified', )
    list_display = ('name', 'type', 'master', 'date_created', 'date_modified')
    list_filter = ('type', )
    search_fields = ('name', 'master')
    inlines = [RecordInline, DomainMetadataInline, CryptoKeyInline]
    
    def queryset(self, request):
        qs = super(DomainAdmin, self).queryset(request)
        if not request.user.is_superuser:
            # Non-superusers see the domains they have created
            qs = qs.filter(name__created_by=request.user)
        return qs
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.save()

admin.site.register(cache.get_model('powerdns_manager', 'Domain'), DomainAdmin)



class TsigKeyAdmin(admin.ModelAdmin):
    fieldsets = (
        ('', {
            'fields' : ('name', 'algorithm', 'secret', ),
        }),
        ('Info', {
            'classes' : ('collapse',),
            'fields' : ('date_created', 'date_modified', ),
        }),
    )
    readonly_fields = ('date_created', 'date_modified')
    list_display = ('name', 'algorithm', 'date_created', 'date_modified')
    list_filter = ('algorithm', )
    search_fields = ('name', )
    
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
    fields = ('ip', 'nameserver', 'account')
    readonly_fields = ('date_created', 'date_modified')
    list_display = ('ip', 'nameserver', 'account', 'date_created', 'date_modified')
    search_fields = ('nameserver', 'account')
    
admin.site.register(cache.get_model('powerdns_manager', 'SuperMaster'), SuperMasterAdmin)

