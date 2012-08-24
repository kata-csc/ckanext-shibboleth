from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IGenshiStreamFilter, IRoutes
from genshi.filters.transform import Transformer
from genshi.input import HTML
from routes import url_for
from pylons import request

import logging
log = logging.getLogger("ckanext.repoze")

class CkanShibbolethPlugin(SingletonPlugin):
    implements(IRoutes, inherit=True)
    implements(IGenshiStreamFilter)

    def filter(self, stream):
        routes = request.environ.get('pylons.routes_dict')
        
        if routes.get('controller') == 'user' and routes.get('action') == 'login':
            shtml = '<li class=""><a href="%s">Shibboleth login</a></li>' % url_for(controller='ckanext.repoze.who.shibboleth.controller:ShibbolethController', action='shiblogin')
            
            stream = stream | Transformer('//ul[@class="nav nav-pills"]').append(HTML(shtml))
        
        return stream
    
    def before_map(self, map):
        controller = 'ckanext.repoze.who.shibboleth.controller:ShibbolethController'
        map.connect('shibboleth', '/user/shiblogin', controller=controller, action='shiblogin')
        return map
    
    def after_map(self, map):
        log.debug(map)
        return map
