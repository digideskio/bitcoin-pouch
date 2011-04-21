from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {"template": "about/about.html"}, name="about"),
    
    url(r'^terms/$', direct_to_template, {"template": "about/terms.html"}, name="terms"),
    url(r'^privacy/$', direct_to_template, {"template": "about/privacy.html"}, name="privacy"),
    url(r'^donate/$', direct_to_template, {"template": "about/donate.html"}, name="donate"),
    
    url(r'^what_next/$', "about.views.what_next", name="what_next"),
)
