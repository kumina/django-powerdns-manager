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
    
    If no ipv4 or ipv6 address is provided, then the client IP address is used
    to update A records (if the client IP is IPv4) or AAAA records (if client IP is IPv6).
    
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
    
    # API key
    
    api_key = form.cleaned_data['api_key']
    
    # Hostname
    
    hostname = form.cleaned_data['hostname']
    
    # If the hostname is missing, the IP addresses of all A and AAAA records
    # of the zone are updated.
    update_all_hosts_in_zone = False
    if not hostname:
        update_all_hosts_in_zone = True
    
    # IP addresses
    
    ipv4 = form.cleaned_data['ipv4']
    ipv6 = form.cleaned_data['ipv6']

    # If IP information is missing, the remote client's IP address will be used.
    if not ipv4 and not ipv6:
        if remote_ipv4:
            ipv4 = remote_ipv4
        if remote_ipv6:
            ipv6 = remote_ipv6
    
    # All required data is good. Process the request.
    
    DynamicZone = cache.get_model('powerdns_manager', 'DynamicZone')
    Record = cache.get_model('powerdns_manager', 'Record')
    
    # Get the relevant dynamic zone instance
    dyn_zone = DynamicZone.objects.get(api_key__exact=api_key)
    
    # Get A and AAAA records
    dyn_rrs = Record.objects.filter(domain=dyn_zone.domain, type__in=('A', 'AAAA'))
    if not dyn_rrs:
        return HttpResponseNotFound('A or AAAA resource records not found')
    
    # Check existence of hostname
    if hostname:
        hostname_exists = False
        for rr in dyn_rrs:
            if rr.name == hostname:
                hostname_exists = True
                break
        if not hostname_exists:
            return HttpResponseNotFound('error:Hostname not found: %s' % hostname)
    
    # Update the IPs
    
    rr_has_changed = False
    
    if update_all_hosts_in_zone:    # No hostname supplied
        for rr in dyn_rrs:
            
            # Try to update A records
            if rr.type == 'A' and ipv4:
                rr.content = ipv4
                rr_has_changed = True
            
            # Try to update AAAA records
            elif rr.type == 'AAAA' and ipv6:
                rr.content = ipv6
                rr_has_changed = True
            
            rr.save()
        
    else:    # A hostname is supplied
        for rr in dyn_rrs:
            if rr.name == hostname:
                
                # Try to update A records
                if rr.type == 'A' and ipv4:
                    rr.content = ipv4
                    rr_has_changed = True
            
                # Try to update AAAA records
                elif rr.type == 'AAAA' and ipv6:
                    rr.content = ipv6
                    rr_has_changed = True
                
                rr.save()
    
    if rr_has_changed:
        return HttpResponse('Success')
    else:
        return HttpResponseNotFound('error:No suitable resource record found')


@csrf_exempt
def api_v1_records_view(request, name, type=False, return_format=False):
    # Sanitize all elements of the input
    if request.method not in ['GET','POST','PUT','DELETE']:
        return HttpResponseNotAllowed(['GET','POST','PUT','DELETE'])

    if return_format:
        return_format = return_format.lstrip('.')
    else:
        return_format = 'zone'
    if return_format not in ['zone']:
        return HttpResponseNotFound('Return format %s unknown' % return_format)

    try:
        content_search = request.REQUEST['content_search']
    except KeyError:
        content_search = None

    try:
        content_match = request.REQUEST['content_match']
    except KeyError:
        content_match = None
    if content_match and content_search:
        return HttpResponseBadRequest('Both "content_search" and "content_match" are requested')

    try:
        content_set = request.REQUEST['content_set']
    except KeyError:
        content_set = None

    try:
        ttl_set = request.REQUEST['ttl_set']
    except KeyError:
        ttl_set = None

    if (ttl_set or content_set) and request.method in ['DELETE','GET']:
        return HttpResponseBadRequest('HTTP %s sent, but set parameters are included in the request')

    if type:
        type = type.upper()

    try:
        api_key = request.META['HTTP_X_PDNS_APIKEY']
    except KeyError:
        return HttpResponseBadRequest('No X-PDNS-APIKEY header sent')

    DynamicZone = cache.get_model('powerdns_manager', 'DynamicZone')
    Record = cache.get_model('powerdns_manager', 'Record')

    # Get all the records associated with name (and type)
    try:
        dyn_zone = DynamicZone.objects.get(api_key__exact=api_key)
    except:
        return HttpResponseNotFound('api_key invalid')

    # Filter on what the user searches for
    dyn_rrs = Record.objects.filter(domain=dyn_zone.domain, name=name)
    resp = 'records of %s IN' % name
    if type:
        dyn_rrs = dyn_rrs.filter(type=type)
        resp += ' ' + type
    if content_search:
        dyn_rrs = dyn_rrs.filter(content__contains=content_search)
        resp += ' with (partial) content %s' % content_search
    if content_match:
        dyn_rrs = dyn_rrs.filter(content__exact=content_match)
        resp += ' with content %s' % content_match

    if request.method == 'GET':
        if dyn_rrs:
            res = ''
            for rr in dyn_rrs:
                res += rr.as_(return_format) + '\n'
            return HttpResponse(res)

        return HttpResponseNotFound('No %s found' % resp)

    if request.method == 'DELETE':
        if not dyn_rrs:
            return HttpResponse('')
        # if there is no type set, we refuse to remove records that are 'zone'
        # records (SOA, NS, MX etc..)
        if not type and dyn_zone.domain == dyn_rrs[0].name:
            return HttpResponseBadRequest('Cowardly refusing to remove all zone-records')

        # Sanity checking done, pulling the trigger
        res = ''
        for rr in dyn_rrs:
            res += rr.as_(return_format)
            rr.delete()
        return HttpResponse(res)

    # When we're here in the code-flow, there is either an addition or a change
    # requested. Let's do some checking for all the data we need
    if not type:
        return HttpResponseBadRequest('No record type supplied')

    if request.method == 'POST':
        if content_search or content_match:
            return HttpResponseBadRequest('Searching or Matching of content requested')
        if not content_set:
            return HttpResponseBadRequest('No content_set parameter in request')

        if len(dyn_rrs.filter(content=content_set)) > 0: # there exists a record
            return HttpResponse('There exists %s with value %s, doing nothing' %
                (resp, content_set))

        if not ttl_set:
            ttl_set = dyn_zone.domain.get_minimum_ttl()

        record = Record( name = name,
                type = type,
                domain = dyn_zone.domain,
                content = content_set,
                ttl = ttl_set
                )
        record.save()
        return HttpResponse(record.as_(return_format))

    if request.method == 'PUT':
        if (not content_search and not content_match) and len(dyn_rrs) > 1:
            return HttpResponseBadRequest('More than one %s found, please supply content_search or content_match parameters'
                    % resp)

        if len(dyn_rrs) == 1:
            if content_set:
                dyn_rrs[0].content = content_set
            if ttl_set:
                dyn_rrs[0].ttl = ttl_set
            dyn_rrs[0].save()
            return HttpResponse(dyn_rrs[0].as_(return_format))

        if len(dyn_rrs) == 0:
            return HttpResponseBadRequest('There exists no %s, doing nothing' %
                    resp)

#@csrf_exempt
#def api_v1_zone_view(request, name, action, return_format=False):
