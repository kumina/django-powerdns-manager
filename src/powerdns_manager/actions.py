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

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django import template
from django.core.exceptions import PermissionDenied
from django.contrib.admin import helpers
from django.contrib.admin.util import get_deleted_objects, model_ngettext
from django.db import router
from django.shortcuts import render_to_response
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy, ugettext as _
from django.contrib import messages
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models.loading import cache

from powerdns_manager.forms import ZoneTypeSelectionForm
from powerdns_manager.forms import TtlSelectionForm



# Action for
# - set change date
# - set serial (?)
# - set TTL to 300, 3600, 86400
#
#def test_action(modeladmin, request, queryset):
#    messages.add_message(request, messages.INFO, 'The test action was successful.')
#test_action.short_description = "Test Action"


def set_domain_type_bulk(modeladmin, request, queryset):
    """Actions that sets the domain type on the selected Domain instances.
    
    This action first displays a page which provides a dropdown box for the
    user to select the domain type and then sets the new domain type on the
    sele3cted objects.
    
    It checks if the user has change permission.
    
    Based on: https://github.com/django/django/blob/1.4.2/django/contrib/admin/actions.py
    
    Important
    ---------
    In order to work requires some special form fields (see the template).
    
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label
    
    # Check that the user has change permission for the Domain model
    if not modeladmin.has_change_permission(request):
        raise PermissionDenied
    
    # The user has selected a new domain type through the
    # forms.ZoneTypeSelectionForm form. Make the changes to the selected
    # objects and return a None to display the change list view again.
    #if request.method == 'POST':
    if request.POST.get('post'):
        domain_type = request.POST.get('domaintype')
        n = queryset.count()
        
        if n and domain_type:
            for obj in queryset:
                obj.type = domain_type
                obj.save()
                obj_display = force_unicode(obj)
                modeladmin.log_change(request, obj, obj_display)
            messages.info(request, 'Successfully updated %d domains.' % n)
        # Return None to display the change list page again.
        return None
    
    info_dict = {
        'form': ZoneTypeSelectionForm(),
        'queryset': queryset,
        'opts': opts,
        'app_label': app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
    }
    return render_to_response(
        'powerdns_manager/actions/set_domain_type.html', info_dict, context_instance=RequestContext(request), mimetype='text/html')
set_domain_type_bulk.short_description = "Set domain type"



def set_ttl_bulk(modeladmin, request, queryset):
    """Actions that resets TTL information on all resource records of the zone
    to the specified value.
    
    This action first displays a page which provides an input box to enter
    the new TTL.
    
    It checks if the user has change permission.
    
    Based on: https://github.com/django/django/blob/1.4.2/django/contrib/admin/actions.py
    
    Important
    ---------
    In order to work requires some special form fields (see the template).
    
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label
    
    Domain = cache.get_model('powerdns_manager', 'Domain')
    Record = cache.get_model('powerdns_manager', 'Record')
    
    perm_domain_change = '%s.%s' % (opts.app_label, opts.get_change_permission())
    perm_record_change = '%s.change_record' % opts.app_label
    
    if not request.user.has_perms([perm_domain_change, perm_record_change]):
        raise PermissionDenied
    
    # Check that the user has change permission for the Re model
    if not modeladmin.has_change_permission(request):
        raise PermissionDenied
    
    # The user has set a new TTL value through the forms.TtlSelectionForm form.
    # Make the changes to the selected objects and return a None to display the
    # change list view again.
    #if request.method == 'POST':
    if request.POST.get('post'):
        form = TtlSelectionForm(request.POST)
        if form.is_valid():
            new_ttl = form.cleaned_data['new_ttl']
            reset_zone_minimum = form.cleaned_data['reset_zone_minimum']
            
            n = queryset.count()
            record_count = 0
            
            if n and new_ttl:
                for domain_obj in queryset:
                    # Find all resource records of this domain
                    qs = Record.objects.filter(domain=domain_obj)
                    # Now set the new TTL
                    for rr in qs:
                        rr.ttl = int(new_ttl)
                        # If this is the SOA record and ``reset_zone_minimum`` has
                        # been checked, set the minimum TTL of the SOA record equal
                        # to the ``new_ttl`` value
                        #
                        # Important: We do not call ``models.Domain.set_minimum_ttl()``
                        # because we edit the SOA record here.
                        #
                        if reset_zone_minimum and rr.type == 'SOA':
                            bits = rr.content.split()
                            # SOA content:  primary hostmaster serial refresh retry expire default_ttl
                            bits[6] = str(new_ttl)
                            rr.content = ' '.join(bits)
                        # Save the resource record
                        rr.save()
                        rr_display = force_unicode(rr)
                        modeladmin.log_change(request, rr, rr_display)
                    record_count += len(qs)
                messages.info(request, 'Successfully updated %d zones (%d total records).' % (n, record_count))
            # Return None to display the change list page again.
            return None
    else:
        form = TtlSelectionForm()
    
    info_dict = {
        'form': form,
        'queryset': queryset,
        'opts': opts,
        'app_label': app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
    }
    return render_to_response(
        'powerdns_manager/actions/set_ttl.html', info_dict, context_instance=RequestContext(request), mimetype='text/html')
set_ttl_bulk.short_description = "Set Resource Records TTL"



def force_serial_update(modeladmin, request, queryset):
    """Action that updates the serial resets TTL information on all resource
    records of the selected zones.
    """
    for domain in queryset:
        domain.update_serial()
    n = queryset.count()
    messages.info(request, 'Successfully updated %d zones.' % n)
force_serial_update.short_description = "Force serial update"


