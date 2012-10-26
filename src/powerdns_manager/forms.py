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
from django.db.models.loading import cache
from django.utils.translation import ugettext_lazy as _



class BaseRecordModelForm(forms.ModelForm):
    """Base ModelForm for Record instances.
    
    """
    class Meta:
        model = cache.get_model('powerdns_manager', 'Record')
    
    def clean(self):
        """ModelForm clean code for all Record ModelForms.
        
        1) Makes sure the RR's name is within the current zone.
        
        For instance, if the zone origin is 'centos.example.org', the user
        will not be able to add records with a name 'example.org'. Such a
        name would belong to the parent zone and is bogus information if
        added to the current zone.
        
        """
        # Check 1: Makes sure the RR's name is within the current zone.
        
        # This ensures that we do not catch a SOA record, for which the name
        # is added in the SoaRecordModelForm.save(). A SOA record will never
        # have a bogus name, since it is not user-editable. 
        if not self.cleaned_data.has_key('name'):
            return self.cleaned_data
        
        name = self.cleaned_data.get('name')
        domain = self.cleaned_data.get('domain')
        if name and domain:
            if len(name.split('.')) < len(domain.name.split('.')):
                msg = 'Invalid record name. This name belongs to a parent zone.'
                self._errors["name"] = self.error_class([msg])
        
        return self.cleaned_data



class SoaRecordModelForm(BaseRecordModelForm):
    """ModelForm for SOA resource records.
    
    By default, PowerDNS expects the content of the SOA records to contain the
    following information:
    
        primary hostmaster serial refresh retry expire default_ttl
    
    This is too inconvenient to edit.
    
    See: http://doc.powerdns.com/types.html#soa-type
    
    To deal with this problem we add separate form fields to the ModelForm
    for each one of the pieces of data that form the SOA RR content above.
    
    When the form is initialized, these fields get their initial values from
    the SOA RR content (see __init__() below).
    
    When the SOA RR is saved, the values of these extra fields
    are concatenated in save() to form the SOA RR content that PowerDNS expects
    to find stored in the database.
    
    Also, if TTl information is missing, then the default TTL (mandatory field)
    is used.
    
    """
    primary = forms.CharField(max_length=96, initial='', required=True, label=_('primary nameserver'), help_text="""The name of the name server that was the original or primary source of data for this zone.""")
    hostmaster = forms.CharField(max_length=64, initial='', required=True, label=_('hostmaster mailbox'), help_text="""A name which specifies the mailbox of the person responsible for this zone. This should be specified in the mailbox-as-domain-name format where the `@' character is replaced with a dot. Example: hostmaster.domain.tld represents hostmaster@domain.tld""")
    serial = forms.IntegerField(min_value=1, initial=1, required=True, label=_('serial'), widget=forms.TextInput(attrs={'readonly': 'readonly'}), help_text="""The serial is generated automatically and is not user-editable. The serial is a "version number" for this zone. DNS servers that rely on AXFR for zone transfers use this to determine when updates have occurred. Popular values to use are the Unix timestamp or a date in the form YYYYMMDD.""")
    refresh = forms.IntegerField(min_value=300, initial=28800, required=True, label=_('refresh'), help_text="""The number of seconds after which slave nameservers should check to see if this zone has been changed. If the zone's serial number has changed, the slave nameserver initiates a zone transfer. Example: 28800""")
    retry = forms.IntegerField(min_value=300, initial=7200, required=True, label=_('retry'), help_text="""This specifies the number of seconds a slave nameserver should wait before retrying if it attmepts to transfer this zone but fails. Example: 7200""")
    expire = forms.IntegerField(min_value=300, initial=604800, required=True, label=_('expire'), help_text="""If for expire seconds the primary server cannot be reached, all information about the zone is invalidated on the secondary servers (i.e., they are no longer authoritative for that zone). Example: 604800""")
    default_ttl = forms.IntegerField(min_value=300, initial=86400, required=True, label=_('minimum TTL'), help_text="""The minimum TTL field that should be exported with any RR from this zone. If any RR in the database has a lower TTL, this TTL is sent instead. Example: 86400""")

    def __init__(self, *args, **kwargs):
        """ModelForm constructor.
        
        If the user edits an existing SOA RR throught the InlineModelAdmin,
        the following code reads the existing content of the ``Record.content``
        field, splits the information into pieces, and fills the initial data
        of the extra fields we have added to the form.
        
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
    
    def save(self, *args, **kwargs):
        """Saves the SOA RR ModelForm.
        
        Model fields that were not editable in the admin interface are set here.
        
        1) The SOA type is set.
        
        2) The values of these extra SOA-specific fields are concatenated
        in order to form the SOA RR content that PowerDNS expects to find
        stored in the database.
        
        3) The TTL field, if missing, is set equal to the ``default_ttl``
        form field.
        
        4) Sets the ``name`` field of the SOA record equal to the name of the
        associated domain. PowerDNS Manager allows only one SOA RR per zone.
        The ``name`` field of the SOA record is not editable in the ModelAdmin.
        
        """
        self.instance.type = 'SOA'
        
        self.instance.content = '%s %s %d %s %s %s %s' % (
            self.cleaned_data.get('primary'),
            self.cleaned_data.get('hostmaster'),
            int(time.time()),
            self.cleaned_data.get('refresh'),
            self.cleaned_data.get('retry'),
            self.cleaned_data.get('expire'),
            self.cleaned_data.get('default_ttl')
        )
        
        if not self.instance.ttl:
            self.instance.ttl = self.cleaned_data.get('default_ttl')
        
        domain = self.cleaned_data.get('domain')
        self.instance.name = domain.name
        
        return super(SoaRecordModelForm, self).save(*args, **kwargs)
        

#class SoaRecordInlineModelFormset(BaseInlineFormSet):
#    """Inline formset for SOA resource records.
#    
#    Here we set the prefix ``soa`` for the formset that contain SOA records.
#    This is because there are two inlines (SoaRecordInline, RecordInline)
#    based on the same model (Record).
#    
#    This model form is used in the SoaRecordInline, which facilitates editing
#    the SOA resource record of the zone.
#    
#    """
#    model = cache.get_model('powerdns_manager', 'Record')
#    
#    @classmethod
#    def get_default_prefix(cls):
#        default_prefix = super(SoaRecordInlineModelFormset, cls).get_default_prefix()
#        return 'soa-%s' % default_prefix


class NsRecordModelForm(BaseRecordModelForm):
    """ModelForm for NS resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'NS'
        return super(NsRecordModelForm, self).save(*args, **kwargs)

    
class MxRecordModelForm(BaseRecordModelForm):
    """ModelForm for MX resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'MX'
        return super(MxRecordModelForm, self).save(*args, **kwargs)


class SrvRecordModelForm(BaseRecordModelForm):
    """ModelForm for SRV resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'SRV'
        return super(SrvRecordModelForm, self).save(*args, **kwargs)
    

class ARecordModelForm(BaseRecordModelForm):
    """ModelForm for A resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'A'
        return super(ARecordModelForm, self).save(*args, **kwargs)


class AaaaRecordModelForm(BaseRecordModelForm):
    """ModelForm for AAAA resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'AAAA'
        return super(AaaaRecordModelForm, self).save(*args, **kwargs)


class CnameRecordModelForm(BaseRecordModelForm):
    """ModelForm for CNAME resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'CNAME'
        return super(CnameRecordModelForm, self).save(*args, **kwargs)


class PtrRecordModelForm(BaseRecordModelForm):
    """ModelForm for PTR resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'PTR'
        return super(PtrRecordModelForm, self).save(*args, **kwargs)


class TxtRecordModelForm(BaseRecordModelForm):
    """ModelForm for TXT resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'TXT'
        return super(TxtRecordModelForm, self).save(*args, **kwargs)


class DsRecordModelForm(BaseRecordModelForm):
    """ModelForm for DS resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'DS'
        return super(DsRecordModelForm, self).save(*args, **kwargs)


class CertRecordModelForm(BaseRecordModelForm):
    """ModelForm for CERT resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'CERT'
        return super(CertRecordModelForm, self).save(*args, **kwargs)


class HinfoRecordModelForm(BaseRecordModelForm):
    """ModelForm for HINFO resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'HINFO'
        return super(HinfoRecordModelForm, self).save(*args, **kwargs)


class LocRecordModelForm(BaseRecordModelForm):
    """ModelForm for LOC resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'LOC'
        return super(LocRecordModelForm, self).save(*args, **kwargs)


class SpfRecordModelForm(BaseRecordModelForm):
    """ModelForm for SPF resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'SPF'
        return super(SpfRecordModelForm, self).save(*args, **kwargs)


class SshfpRecordModelForm(BaseRecordModelForm):
    """ModelForm for SSHFP resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'SSHFP'
        return super(SshfpRecordModelForm, self).save(*args, **kwargs)


class RpRecordModelForm(BaseRecordModelForm):
    """ModelForm for RP resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'RP'
        return super(RpRecordModelForm, self).save(*args, **kwargs)


class NaptrRecordModelForm(BaseRecordModelForm):
    """ModelForm for NAPTR resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'NAPTR'
        return super(NaptrRecordModelForm, self).save(*args, **kwargs)


class AfsdbRecordModelForm(BaseRecordModelForm):
    """ModelForm for AFSDB resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'AFSDB'
        return super(AfsdbRecordModelForm, self).save(*args, **kwargs)


class DnskeyRecordModelForm(BaseRecordModelForm):
    """ModelForm for DNSKEY resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'DNSKEY'
        return super(DnskeyRecordModelForm, self).save(*args, **kwargs)


class KeyRecordModelForm(BaseRecordModelForm):
    """ModelForm for KEY resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'KEY'
        return super(KeyRecordModelForm, self).save(*args, **kwargs)


class NsecRecordModelForm(BaseRecordModelForm):
    """ModelForm for NSEC resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'NSEC'
        return super(NsecRecordModelForm, self).save(*args, **kwargs)


class RrsigRecordModelForm(BaseRecordModelForm):
    """ModelForm for RRSIG resource records."""

    def save(self, *args, **kwargs):
        self.instance.type = 'RRSIG'
        return super(RrsigRecordModelForm, self).save(*args, **kwargs)



class ZoneImportForm(forms.Form):
    """This form is used to import zone files through the ``import_zone_view``.
    
    """
    origin = forms.CharField(max_length=128, initial='', required=False, label=_('Origin'), help_text="""Enter the origin, otherwise make sure this information is available in your zone file either by the $ORIGIN directive or by using an FQDN in the name field of each record. (optional)""")
    zonetext = forms.CharField(widget=forms.Textarea, initial='', required=True, label=_('Zone file'), help_text="""Paste the zone file text. (required)""")
    overwrite = forms.BooleanField(required=False, label=_('Overwrite'), help_text="""If checked, existing zone will be replaced by this one. Proceed with caution.""")

