import unittest

from routes import url_for

import ckan.model as model
from ckan.tests.functional.base import FunctionalTestCase
from ckanext.repoze.who.shibboleth.plugin import make_identification_plugin, SHIBBOLETH
import ckanext.kata.model as kata_model

SESSION_FIELD = 'Shib-Session-ID'
SESSION_FIELD_VAL = '_7ec5a681e6dbae627c1cefcc7cb4d56a'
MAIL_FIELD = 'mail'
FULLNAME_FIELD = 'cn'
AUTH_FIELD = 'AUTH_TYPE'
EPPN_FIELD = 'eppn'
FIRSTNAME_FIELD = 'displayName'
SURNAME_FIELD = 'sn'
ORGANIZATION_FIELD = 'schacHomeOrganization'
MOBILE_FIELD = 'mobile'
TELEPHONE_FIELD = 'telephoneNumber'

controller = 'ckanext.repoze.who.shibboleth.controller:ShibbolethController'
login_url = url_for(controller=controller, action='shiblogin')
logout_url = url_for(controller='user', action='logout')


def create_plugin(kwargs={}):
    defaults = kwargs
    defaults['session'] = SESSION_FIELD
    defaults['mail'] = MAIL_FIELD
    defaults['fullname'] = FULLNAME_FIELD
    defaults['eppn'] = EPPN_FIELD
    defaults['firstname'] = FIRSTNAME_FIELD
    defaults['surname'] = SURNAME_FIELD
    defaults['organization'] = ORGANIZATION_FIELD
    defaults['mobile'] = MOBILE_FIELD
    defaults['telephone'] = TELEPHONE_FIELD

    return make_identification_plugin(**defaults)

# TODO: Fix
# class TestShibbolethUrls(FunctionalTestCase, unittest.TestCase):
#     def setUp(self, *args, **kwargs):
#         self.plugin = create_plugin(**kwargs)
#         kata_model.setup()
#
#     def test_login(self):
#         headers = {AUTH_FIELD: 'shibboleth',
#                    SESSION_FIELD: SESSION_FIELD_VAL,
#                    MAIL_FIELD: 'foolish@bar.com',
#                    FULLNAME_FIELD: 'Fool Bar'}
#
#         resp = self.app.get(login_url, extra_environ=headers).follow()
#         self.assertEqual(self.app.get('/user/dashboard').status, 200)
#
#
#     def test_logout(self):
#         headers = {AUTH_FIELD: 'shibboleth',
#                     SESSION_FIELD: SESSION_FIELD_VAL,
#                     MAIL_FIELD: 'foolish@bar.com',
#                     FULLNAME_FIELD: 'Fool Bar'}
#
#         resp = self.app.get(login_url, extra_environ=headers)
#         self.assertEqual(self.app.get('/user/dashboard').status, 200)
#
#         resp = self.app.get('/user/_logout').follow()
#         self.assertEqual(self.app.get('/user/dashboard').status, 302)

class TestShibbolethPlugin(unittest.TestCase):
    plugin = None

    def setUp(self, *args, **kwargs):
        self.plugin = create_plugin(**kwargs)
        kata_model.setup()

    def test_plugin_field_names(self):
        self.assertNotEqual(self.plugin, None)
        self.assertEqual(self.plugin.session, SESSION_FIELD)
        self.assertEqual(self.plugin.eppn, EPPN_FIELD)
        self.assertEqual(self.plugin.mail, MAIL_FIELD)
        self.assertEqual(self.plugin.fullname, FULLNAME_FIELD)

    def test_plugin_created(self):
        self.assertNotEqual(self.plugin, None)

    def test_shib_session(self):
        env_dict = {SESSION_FIELD: SESSION_FIELD_VAL, MAIL_FIELD: u'foo@bar.com',
                    FULLNAME_FIELD: u'Foo Bar', AUTH_FIELD: SHIBBOLETH}
        self.assertEqual(self.plugin.is_shib_session(env_dict), True)

        env_dict = {SESSION_FIELD: SESSION_FIELD_VAL, MAIL_FIELD: u'foo@bar.com',
                    FULLNAME_FIELD: u'Foo Bar', AUTH_FIELD: 'FooBarAuth'}
        self.assertEqual(self.plugin.is_shib_session(env_dict), False)

    def test_identify_without_shib_session(self):
        env = dict(PATH_INFO='/user/shiblogin')
        identity = self.plugin.identify(env)

        self.assertEqual(identity, {})

    def test_create_user(self):
        import re
        user_dict = {EPPN_FIELD: u'foo@bar.com',
                     MAIL_FIELD: u'foo@bar.com',
                     FULLNAME_FIELD: 'Foo Bar',
                     AUTH_FIELD: SHIBBOLETH}
        #username = re.sub('[.@]', '_', user_dict[MAIL_FIELD])
        username = unicode(user_dict[FULLNAME_FIELD], errors='ignore').lower().replace(' ', '_')
        user = self.plugin._get_or_create_user(user_dict)

        self.assertNotEqual(user, {})
        self.assertEqual(user.openid, user_dict[EPPN_FIELD])
        self.assertEqual(user.name, username)
        self.assertEqual(user.fullname, user_dict[FULLNAME_FIELD])

    def test_get_or_create_user(self):
        import re
        user_dict = {EPPN_FIELD: u'newfoo@bar.com',
                     MAIL_FIELD: u'newfoo@bar.com',
                     FULLNAME_FIELD: 'New Foo Bar',
                     AUTH_FIELD: SHIBBOLETH}
        #username = re.sub('[.@]', '_', user_dict[MAIL_FIELD])
        username = unicode(user_dict[FULLNAME_FIELD], errors='ignore').lower().replace(' ', '_')

        user = model.User(name = username,
                          fullname = user_dict[FULLNAME_FIELD],
                          email = user_dict[MAIL_FIELD],
                          openid = user_dict[EPPN_FIELD])

        model.Session.add(user)
        model.Session.commit()

        user_2 = self.plugin._get_or_create_user(user_dict)

        self.assertNotEqual(user_2, {})
        self.assertEqual(user.id, user_2.id)
        self.assertEqual(user.openid, user_2.openid)
        self.assertEqual(user.fullname, user_2.fullname)
        self.assertEqual(user.email, user_2.email)
        self.assertEqual(user.name, user_2.name)

    def test_identity_with_invalid_shib_session(self):
        # Wrong login url
        identity_1 = self.plugin.identify({'PATH_INFO':'/foo/gives/a/bar/',
                                        SESSION_FIELD:SESSION_FIELD_VAL,
                                        MAIL_FIELD:u'foo@bar.com',
                                        FULLNAME_FIELD:u'Foo Bar',
                                        AUTH_FIELD:'shibboleth'})

        # Wrong authentication type
        identity_2 = self.plugin.identify({'PATH_INFO':login_url,
                                        SESSION_FIELD:SESSION_FIELD_VAL,
                                        MAIL_FIELD:u'foo@bar.com',
                                        FULLNAME_FIELD:u'Foo Bar',
                                        AUTH_FIELD:'FooAuth'})

        # Missing name field
        identity_3 = self.plugin.identify({'PATH_INFO':login_url,
                                        SESSION_FIELD:SESSION_FIELD_VAL,
                                        MAIL_FIELD:u'foo@bar.com',
                                        AUTH_FIELD:SHIBBOLETH})

        # Missing mail field
        identity_4 = self.plugin.identify({'PATH_INFO':login_url,
                                        SESSION_FIELD:SESSION_FIELD_VAL,
                                        FULLNAME_FIELD:u'Foo Bar',
                                        AUTH_FIELD:SHIBBOLETH})

        # Missing session field
        identity_5 = self.plugin.identify({'PATH_INFO':login_url,
                                        MAIL_FIELD:u'foo@bar.com',
                                        FULLNAME_FIELD:u'Foo Bar',
                                        AUTH_FIELD:SHIBBOLETH})

        self.assertEqual(identity_1, {})
        self.assertEqual(identity_2, {})
        self.assertEqual(identity_3, {})
        self.assertEqual(identity_4, {})
        self.assertEqual(identity_5, {})

    # TODO: Fix
    # def test_identity_with_valid_shib_session(self):
    #     eppn_val = u'foo@bar.com'
    #     mail_val = u'foo@bar.com'
    #     name_val = 'Foo Bar'
    #
    #     identity = self.plugin.identify({'PATH_INFO': login_url,
    #                                     SESSION_FIELD: SESSION_FIELD_VAL,
    #                                     EPPN_FIELD: eppn_val,
    #                                     MAIL_FIELD: mail_val,
    #                                     FULLNAME_FIELD: name_val,
    #                                     AUTH_FIELD: SHIBBOLETH})
    #
    #     self.assertNotEqual(identity, {})
    #     self.assertEqual(identity['email'], mail_val)
    #     self.assertEqual(identity['login'], mail_val)
    #     self.assertEqual(identity['fullname'], mail_val)
    #     self.assertEqual(identity['password'], '')
    #     self.assertEqual(identity['repoze.who.plugins.openid.userid'], mail_val)

    def test_remember(self):
        self.assertEqual(self.plugin.remember({}, {}), None)

    def test_forget(self):
        self.assertEqual(self.plugin.forget({}, {}), None)
