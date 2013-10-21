import ckan.controllers.user as user
import ckan.lib.base as base

class ShibbolethController(user.UserController):
    def shiblogin(self):
        # This whole controller class doesn't seem to do anything.
        # Juho Lehtonen 26.9.2013
        #return self.login()
        return base.h.redirect_to(controller='user',
                                  action='read',
                                  id=base.c.userobj.name)