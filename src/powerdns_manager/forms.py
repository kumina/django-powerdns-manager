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

import time

from django import forms
from django.forms.models import BaseInlineFormSet
from django.forms.models import modelformset_factory
from django.db.models.loading import cache
from django.utils.translation import ugettext_lazy as _



class SoaRecordModelForm(forms.ModelForm):
    """ModelForm for SOA resource records.
    
    By default, PowerDNS expects the content of the SOA records to contain the
    following information:
    
        primary hostmaster serial refresh retry expire default_ttl
    
    This is way too inconvenient to edit.
    
    See: http://doc.powerdns.com/types.html#soa-type
    
    To deal with this problem we add separate form fields to the modelform
    for each one of the pieces of data that form the SOA RR content above.
    
    When the form is initialized, these fields get their initial values from the
    SOA RR content (see __init__() below).
    
    When the SOA RR is saved, the values of these extra fields
    are concatenated to form the SOA RR content that PowerDNS expects to find
    stored in the database. (see admin.DomainAdmin.save_formset())
    
    This model form is used in the SoaRecordInline, which facilitates editing
    the SOA resource record of the zone.
      
    """
    primary = forms.CharField(max_length=96, initial='', required=True, label=_('primary nameserver'), help_text="""The name of the name server that was the original or primary source of data for this zone.""")
    hostmaster = forms.CharField(max_length=64, initial='', required=True, label=_('hostmaster mailbox'), help_text="""A name which specifies the mailbox of the person responsible for this zone. This should be specified in the mailbox-as-domain-name format where the `@' character is replaced with a dot. Example: hostmaster.domain.tld represents hostmaster@domain.tld""")
    serial = forms.IntegerField(min_value=1, initial=1, required=True, label=_('serial'), widget=forms.TextInput(attrs={'readonly': 'readonly'}), help_text="""The serial is generated automatically and is not user-editable. The serial is a "version number" for this zone. DNS servers that rely on AXFR for zone transfers use this to determine when updates have occurred. Popular values to use are the Unix timestamp or a date in the form YYYYMMDD.""")

    refresh = forms.IntegerField(min_value=300, initial=28800, required=True, label=_('refresh'), help_text="""The number of seconds after which slave nameservers should check to see if this zone has been changed. If the zone's serial number has changed, the slave nameserver initiates a zone transfer. Example: 28800""")
    retry = forms.IntegerField(min_value=300, initial=7200, required=True, label=_('retry'), help_text="""This specifies the number of seconds a slave nameserver should wait before retrying if it attmepts to transfer this zone but fails. Example: 7200""")
    expire = forms.IntegerField(min_value=300, initial=604800, required=True, label=_('expire'), help_text="""If for expire seconds the primary server cannot be reached, all information about the zone is invalidated on the secondary servers (i.e., they are no longer authoritative for that zone). Example: 604800""")
    default_ttl = forms.IntegerField(min_value=300, initial=86400, required=True, label=_('minimum TTL'), help_text="""The minimum TTL field that should be exported with any RR from this zone. If any RR in the database has a lower TTL, this TTL is sent instead. Example: 86400""")

    class Meta:
        model = cache.get_model('powerdns_manager', 'Record')

    def __init__(self, *args, **kwargs):
        """ModelForm constructor.
        
        If the SOA RR is edited, the following code reads the existing content
        of the ``Record.content`` field, splits the information into pieces,
        and fills the initial data of the extra fields we have added to the form.
        
        See: http://doc.powerdns.com/types.html#soa-type
        
        """
        if kwargs.has_key('instance'):
            instance = kwargs['instance']
            if instance.pk is not None:    # This check asserts that this is an EDIT
                if instance.type == 'SOA':
                    bits = instance.content.split()
                    kwargs['initial'] = {
                        'primary': bits[0],
                        'hostmaster': bits[1],
                        'serial': bits[2],
                        'refresh': bits[3],
                        'retry': bits[4],
                        'expire': bits[5],
                        'default_ttl': bits[6],
                    }
        super(SoaRecordModelForm, self).__init__(*args, **kwargs)
        
    def clean_hostmaster(self):
        hostmaster = self.cleaned_data.get('hostmaster')
        if hostmaster.find('@') != -1:
            raise forms.ValidationError("""This should be specified in the mailbox-as-domain-name format where the `@' character is replaced with a dot. Example: hostmaster.domain.tld represents hostmaster@domain.tld""")
        return hostmaster
    

class SoaRecordInlineFormset(BaseInlineFormSet):
    """Inline formset for SOA resource records.
    
    Here we set the prefix ``soa`` for the formset that contain SOA records.
    This is because there are two inlines (SoaRecordInline, RecordInline)
    based on the same model (Record).
    
    This model form is used in the SoaRecordInline, which facilitates editing
    the SOA resource record of the zone.
    
    """
    def __init__(self, *args, **kwargs):
        kwargs['prefix'] = 'soa'
        super(SoaRecordInlineFormset, self).__init__(*args, **kwargs)
        
SoaRecordInlineModelFormset = modelformset_factory(
    cache.get_model('powerdns_manager', 'Record'), form=SoaRecordModelForm, formset=SoaRecordInlineFormset)



