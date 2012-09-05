from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IGenshiStreamFilter, IRoutes
from genshi.filters.transform import Transformer
from genshi.input import HTML
from routes import url_for
from pylons import request

import logging
log = logging.getLogger("ckanext.repoze")

def shib_urls():
    return [url_for(controller='user', action='login'),
            url_for(controller='user', action='register'),
            url_for(controller='user', action='logged_out_page')]


class CkanShibbolethPlugin(SingletonPlugin):
    implements(IRoutes, inherit=True)
    implements(IGenshiStreamFilter)

    def filter(self, stream):
        routes = request.environ.get('pylons.routes_dict')
        from ckan.lib.base import request as req
        
        if req.path in shib_urls():
            shtml = '<li class=""><a href="%s">Shibboleth login</a></li>' % url_for(controller='ckanext.repoze.who.shibboleth.controller:ShibbolethController', action='shiblogin')
            
            stream = stream | Transformer('//ul[@class="nav nav-pills"]').append(HTML(shtml))
        
        return stream
    
    def before_map(self, map):
        controller = 'ckanext.repoze.who.shibboleth.controller:ShibbolethController'
        map.connect('shibboleth', '/shibboleth/login', controller=controller, action='shiblogin')
        return map
    
    def after_map(self, map):
        return map
