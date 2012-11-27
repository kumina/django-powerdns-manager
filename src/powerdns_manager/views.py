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
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.db.models.loading import cache
from django.utils.html import mark_safe
from django.core.validators import validate_ipv4_address
from django.core.validators import validate_ipv6_address
from django.core.exceptions import ValidationError

from powerdns_manager.forms import ZoneImportForm
from powerdns_manager.forms import AxfrImportForm
from powerdns_manager.forms import DynamicIPUpdateForm
from powerdns_manager.utils import process_zone_file
from powerdns_manager.utils import process_axfr_response
from powerdns_manager.utils import generate_zone_file



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
            
            try:
                process_zone_file(origin, zonetext, overwrite)
            except Exception, e:
                info_dict = {
                    'strerror': mark_safe(str(e)),
                }
                return render_to_response('powerdns_manager/import/error.html', info_dict, mimetype='text/html')
            return render_to_response('powerdns_manager/import/success.html', {}, mimetype='text/html')
            
    else:
        form = ZoneImportForm() # An unbound form

    info_dict = {
        'form': form,
    }
    return render_to_response(
        'powerdns_manager/import/zone.html', info_dict, context_instance=RequestContext(request), mimetype='text/html')



@login_required
@csrf_protect
def import_axfr_view(request):
    if request.method == 'POST':
        form = AxfrImportForm(request.POST)
        if form.is_valid():
            origin = form.cleaned_data['origin']
            nameserver = form.cleaned_data['nameserver']
            overwrite = form.cleaned_data['overwrite']
            
            try:
                process_axfr_response(origin, nameserver, overwrite)
            except Exception, e:
                info_dict = {
                    'strerror': mark_safe(str(e)),
                }
                return render_to_response('powerdns_manager/import/error.html', {}, mimetype='text/html')
            info_dict = {'is_axfr': True}
            return render_to_response('powerdns_manager/import/success.html', info_dict, mimetype='text/html')
            
    else:
        form = AxfrImportForm() # An unbound form

    info_dict = {
        'form': form,
    }
    return render_to_response(
        'powerdns_manager/import/axfr.html', info_dict, context_instance=RequestContext(request), mimetype='text/html')




@login_required
def export_zone_view(request, origin):
    info_dict = {
        'zone_text': generate_zone_file(origin),
        'origin': origin,
    }
    return render_to_response(
        'powerdns_manager/export/zone.html', info_dict, context_instance=RequestContext(request), mimetype='text/html')



@csrf_exempt
def dynamic_ip_update_view(request):
    """
    
    TODO: explain dynamic IP update options and logic
    
    if hostname is missing, the ips of all A and AAAA records of the zone are changed
    otherwise only the specific record with the name=hostname and provided that the
    correct ip (v4, v6) has been provided for the type of the record (A, AAAA)
    
    curl -k \
        -F "api_key=UBSE1RJ0J175MRAMJC31JFUH" \
        -F "hostname=ns1.centos.example.org" \
        -F "ipv4=10.1.2.3" \
        -F "ipv6=3ffe:1900:4545:3:200:f8ff:fe21:67cf" \
        https://centos.example.org/powerdns/update/

    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    form = DynamicIPUpdateForm(request.POST)
    
    if not form.is_valid():
        return HttpResponseBadRequest(repr(form.errors))
    
    # Determine protocol or REMOTE_ADDR
    remote_ipv4 = None
    remote_ipv6 = None
    try:
        validate_ipv4_address(request.META['REMOTE_ADDR'])
    except ValidationError:
        try:
            validate_ipv6_address(request.META['REMOTE_ADDR'])
        except ValidationError:
            return HttpResponseBadRequest('Cannot determine protocol of remote IP address')
        else:
            remote_ipv6 = request.META['REMOTE_ADDR']
    else:
        remote_ipv4 = request.META['REMOTE_ADDR']
    
    # Gather required information
    
    api_key = form.cleaned_data['api_key']
    hostname = form.cleaned_data['hostname']
    
    ipv4 = form.cleaned_data['ipv4']
    if not ipv4:
        ipv4 = remote_ipv4
    
    ipv6 = form.cleaned_data['ipv6']
    if not ipv6:
        ipv6 = remote_ipv6
    
    # If the hostname is missing, the IP addresses of all A and AAAA records
    # of the zone are updated.
    update_all_hosts_in_zone = False
    if not hostname:
        update_all_hosts_in_zone = True
    
    # All required data is good. Process the request.
    
    DynamicZone = cache.get_model('powerdns_manager', 'DynamicZone')
    Record = cache.get_model('powerdns_manager', 'Record')
    
    # Get the relevant dynamic zone instance
    dyn_zone = DynamicZone.objects.get(api_key__exact=api_key)
    
    # Get A and AAAA records
    dyn_rrs = Record.objects.filter(domain=dyn_zone.domain, type__in=('A', 'AAAA'))
    if not dyn_rrs:
        HttpResponseNotFound('A or AAAA resource records not found')
    
    # Check existence of hostname
    if hostname:
        hostname_exists = False
        for rr in dyn_rrs:
            if rr.name == hostname:
                hostname_exists = True
                break
        if not hostname_exists:
            return HttpResponseNotFound('Hostname not found: %s' % hostname)
    
    # Update the IPs
    if update_all_hosts_in_zone:    # No hostname supplied
        for rr in dyn_rrs:
            
            # Try to update A records
            if ipv4 and rr.type == 'A':
                rr.content = ipv4
            
            # Try to update AAAA records
            elif ipv6 and rr.type == 'AAAA':
                rr.content = ipv6
            
            rr.save()
        
    else:    # A hostname is supplied
        for rr in dyn_rrs:
            if rr.name == hostname:
                
                # Try to update A records
                if ipv4 and rr.type == 'A':
                    rr.content = ipv4
            
                # Try to update AAAA records
                elif ipv6 and rr.type == 'AAAA':
                    rr.content = ipv6
                
                rr.save()
    
    return HttpResponse('Success')

