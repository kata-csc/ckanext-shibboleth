import sys
from ckan.controllers.user import UserController

class ShibbolethController(UserController):
    def shiblogin(self):
        return self.login()