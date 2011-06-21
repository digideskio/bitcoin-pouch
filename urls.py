import os.path
from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.contrib import admin
admin.autodiscover()

from account.openid_consumer import PinaxConsumer

if settings.ACCOUNT_OPEN_SIGNUP:
    signup_view = "account.views.signup"
else:
    signup_view = "signup_codes.views.signup"


urlpatterns = patterns('',
    url(r'^$', "home.views.direct", name="homepage"),
    
    url(r'^admin/invite_user/$', 'signup_codes.views.admin_invite_user', name="admin_invite_user"),
    url(r'^account/signup/$', signup_view, name="acct_signup"),
    
    (r'^about/', include('about.urls')),
    (r'^account/', include('account.urls')),
    (r'^openid/(.*)', PinaxConsumer()),
    (r'^profiles/', include('basic_profiles.urls')),
    (r'^notices/', include('notification.urls')),
    (r'^announcements/', include('announcements.urls')),
    #(r'^socialauth/', include('socialauth.urls')),
    #(r'^admin/(.*)', admin.site.root),
    (r'^api/bitcoind/', include('bitcoind.urls')),
    (r'^js-remote/(.+)', 'django.views.static.serve', {'document_root': os.path.join(settings.PROJECT_ROOT, 'media', 'js-remote')}),
    (r'^js-remote/', direct_to_template, {"template": "js-remote/index.html"})
)

if settings.SERVE_MEDIA:
    urlpatterns += patterns('',
        (r'^site_media/', include('staticfiles.urls')),
    )
