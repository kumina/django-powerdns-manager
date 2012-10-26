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


from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from django.db.models.loading import cache
from django.utils.html import mark_safe

from powerdns_manager.forms import ZoneImportForm
from powerdns_manager.utils import process_zone_file


@login_required
@csrf_protect
def import_zone_view(request):
    if request.method == 'POST': # If the form has been submitted...
        form = ZoneImportForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            origin = form.cleaned_data['origin']
            zonetext = form.cleaned_data['zonetext']
            overwrite = form.cleaned_data['overwrite']
            
            # Check if exists
            Domain = cache.get_model('powerdns_manager', 'Domain')
            try:
                domain_instance = Domain.objects.get(name=origin)
            except Domain.DoesNotExist:
                pass
            else:
                if overwrite:
                    # If ``overwrite`` has been checked, then delete the current zone.
                    domain_instance.delete()
                else:
                    info_dict = {
                        'strerror': mark_safe('Zone already exists. If you wish to replace it with the imported one, check the <em>Overwrite</em> option in the import form.'),
                    }
                    return render_to_response('powerdns_manager/import/error.html', info_dict, mimetype='text/html')
            
            try:
                process_zone_file(origin, zonetext)
            except Exception, e:
                info_dict = {
                    'strerror': str(e),
                }
                return render_to_response('powerdns_manager/import/error.html', info_dict, mimetype='text/html')
            #return HttpResponse('<h1>Success</h1>', content_type="text/html")
            return render_to_response('powerdns_manager/import/success.html', {}, mimetype='text/html')
            
    else:
        form = ZoneImportForm() # An unbound form

    info_dict = {
        'form': form,
    }
    return render_to_response(
        'powerdns_manager/import/zone.html', info_dict, context_instance=RequestContext(request), mimetype='text/html')
    




    
    
    
    
    
    