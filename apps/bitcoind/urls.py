from django.conf.urls.defaults import *
from jsonrpc import jsonrpc_site
import bitcoind.views

urlpatterns = patterns('',
    url(r'^browse/', 'jsonrpc.views.browse', name="jsonrpc_browser"),
    url(r'^$', jsonrpc_site.dispatch, name="jsonrpc_mountpoint"),
)
