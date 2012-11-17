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

from powerdns_manager.forms import ZoneTypeSelectionForm


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
    

    # Display the confirmation page
#    return TemplateResponse(request, modeladmin.delete_selected_confirmation_template or [
#        "admin/%s/%s/delete_selected_confirmation.html" % (app_label, opts.object_name.lower()),
#        "admin/%s/delete_selected_confirmation.html" % app_label,
#        "admin/delete_selected_confirmation.html"
#    ], context, current_app=modeladmin.admin_site.name)
#    
#    
#        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
#        ct = ContentType.objects.get_for_model(queryset.model)
#        return HttpResponseRedirect("/export/?ct=%s&ids=%s" % (ct.pk, ",".join(selected)))
#    action_set_domain_type_bulk.short_description = "Set domain type"





