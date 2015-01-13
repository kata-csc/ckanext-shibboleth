'''
Repoze.who Shibboleth controller
'''

import logging

from pylons.i18n import _

import ckan.controllers.user as user
import ckan.lib.base as base

log = logging.getLogger(__name__)


class ShibbolethController(user.UserController):
    def shiblogin(self):
        if base.c.userobj is not None:
            log.info("Repoze.who Shibboleth controller received userobj %r " % base.c.userobj)
            return base.h.redirect_to(controller='user',
                                      action='read',
                                      id=base.c.userobj.name)
        else:
            log.error("No userobj received in Repoze.who Shibboleth controller %r " % base.c)
            base.h.flash_error(_("No user info received for login"))
            return base.h.redirect_to('/')
