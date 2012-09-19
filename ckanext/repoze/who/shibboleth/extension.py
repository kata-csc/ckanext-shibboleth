from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IGenshiStreamFilter, IRoutes, IConfigurer
from genshi.filters.transform import Transformer
from genshi.input import HTML
from routes import url_for
from pylons import request
import os

import logging
log = logging.getLogger("ckanext.repoze")

class CkanShibbolethPlugin(SingletonPlugin):
    implements(IRoutes, inherit=True)
    implements(IGenshiStreamFilter)
    implements(IConfigurer)

    def filter(self, stream):
        routes = request.environ.get('pylons.routes_dict')
        
        if routes.get('controller') == 'user' and routes.get('action') == 'login':
            shtml = '<li class=""><a href="%s">Shibboleth login</a></li>' % url_for(controller='ckanext.repoze.who.shibboleth.controller:ShibbolethController', action='shiblogin')
            
            stream = stream | Transformer('//ul[@class="nav nav-pills"]').append(HTML(shtml))
        
        return stream

    def update_config(self, config):
        """This IConfigurer implementation causes CKAN to look in the
        ```public``` and ```templates``` directories present in this
        package for any customisations.

        It also shows how to set the site title here (rather than in
        the main site .ini file), and causes CKAN to use the
        customised package form defined in ``package_form.py`` in this
        directory.
        """
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        template_dir = os.path.join(rootdir, 'who', 'shibboleth', 'templates')
        config['extra_template_paths'] = ','.join([template_dir,
                config.get('extra_template_paths', '')])

    def before_map(self, map):
        controller = 'ckanext.repoze.who.shibboleth.controller:ShibbolethController'
        map.connect('shibboleth', '/user/shiblogin', controller=controller, action='shiblogin')
        return map
    
    def after_map(self, map):
        log.debug(map)
        return map
