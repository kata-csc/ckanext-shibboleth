import os
from routes import url_for

import ckan.plugins as p

#import logging
#log = logging.getLogger("ckanext.repoze")

def shib_urls():
    return [url_for(controller='user', action='login'),
            url_for(controller='user', action='register'),
            url_for(controller='user', action='logged_out_page')]


class CkanShibbolethPlugin(p.SingletonPlugin):
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer)

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
        """
        Override IRoutes.before_map()
        """
        controller = 'ckanext.repoze.who.shibboleth.controller:ShibbolethController'
        map.connect('shibboleth',
                    '/shibboleth/login',
                    controller=controller,
                    action='shiblogin')
        return map
    
    def after_map(self, map):
        return map
