from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

# URLs for django.contrib.admin
urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
)

# URLs for powerdns_manager
urlpatterns += patterns('',
    url('^powerdns/', include('powerdns_manager.urls')),
)

