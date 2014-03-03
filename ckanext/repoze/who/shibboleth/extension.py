# import logging
import os

from routes import url_for

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.shibboleth.actions as actions

# log = logging.getLogger(__name__)


def shib_urls():
    return [url_for(controller='user', action='login'),
            url_for(controller='user', action='register'),
            url_for(controller='user', action='logged_out_page')]


class CkanShibbolethPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions, inherit=True)

    def update_config(self, config):
        """
        This IConfigurer implementation causes CKAN to look in the `templates`
        or 'public' directories present in this package for any customisations.
        """
        # FIXME Simplify augmenting path like for 'public' using toolkit
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        template_dir = os.path.join(rootdir, 'who', 'shibboleth', 'templates')
        config['extra_template_paths'] = ','.join([template_dir,
                config.get('extra_template_paths', '')])
        toolkit.add_public_directory(config, 'public')

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
