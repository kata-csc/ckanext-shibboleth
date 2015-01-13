'''
Shibboleth plugin for CKAN
'''

import os

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.shibboleth.actions as actions


class CkanShibbolethPlugin(plugins.SingletonPlugin):
    '''
    Shibboleth plugin for CKAN
    '''

    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions, inherit=True)

    def update_config(self, config):
        """
        This IConfigurer implementation causes CKAN to look in the `templates`
        or 'public' directories present in this package for any customisations.
        """
        toolkit.add_template_directory(config, 'templates')
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
    
    def get_actions(self):
        """ Register actions. """
        return {'user_show': actions.user_show,
                'user_update': actions.user_update,
            #   'user_create': actions.user_create,
        }
