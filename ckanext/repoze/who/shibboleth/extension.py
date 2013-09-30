import os
from routes import url_for

import ckan.plugins as p
import ckanext.shibboleth.actions as actions

#import logging
#log = logging.getLogger("ckanext.repoze")

def shib_urls():
    return [url_for(controller='user', action='login'),
            url_for(controller='user', action='register'),
            url_for(controller='user', action='logged_out_page')]


class CkanShibbolethPlugin(p.SingletonPlugin):
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer)
    p.implements(p.IActions, inherit=True)

    def update_config(self, config):
        """
        This IConfigurer implementation causes CKAN to look in the
        ```templates``` directories present in this package for any
        customisations.

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

    def get_actions(self):
        """ Register actions. """
        return {'user_show': actions.user_show,
                'user_update': actions.user_update,
            #   'user_create': actions.user_create,
        }
