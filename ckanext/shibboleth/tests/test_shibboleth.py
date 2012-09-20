import unittest
from ckan.model import Session, User
from ckanext.repoze.who.shibboleth.plugin import make_identification_plugin, SHIBBOLETH
from ckan.tests.functional.base import FunctionalTestCase

SESSION_FIELD = 'Shib-Session-ID'
SESSION_FIELD_VAL = '_7ec5a681e6dbae627c1cefcc7cb4d56a'
MAIL_FIELD = 'mail'
NAME_FIELD = 'cn'
AUTH_FIELD = 'AUTH_TYPE'

from routes import url_for
controller = 'ckanext.repoze.who.shibboleth.controller:ShibbolethController'
login_url = url_for(controller=controller, action='shiblogin')
logout_url = url_for(controller='user', action='logout')

def create_plugin(kwargs={}):
	defaults = kwargs
	defaults['session'] = SESSION_FIELD
	defaults['mail'] = MAIL_FIELD
	defaults['name'] = NAME_FIELD
	
	return make_identification_plugin(**defaults)

class TestShibbolethUrls(FunctionalTestCase, unittest.TestCase):
	def setUp(self, *args, **kwargs):
		self.plugin = create_plugin(**kwargs)
		
	def test_login(self):
		headers = {AUTH_FIELD:'shibboleth',
					SESSION_FIELD:SESSION_FIELD_VAL,
					MAIL_FIELD:'foolish@bar.com',
					NAME_FIELD:'Fool Bar'}
		
		resp = self.app.get(login_url, extra_environ=headers).follow()
		self.assertEqual(self.app.get('/user/dashboard').status, 200)
		
	
	def test_logout(self):
		headers = {AUTH_FIELD:'shibboleth',
					SESSION_FIELD:SESSION_FIELD_VAL,
					MAIL_FIELD:'foolish@bar.com',
					NAME_FIELD:'Fool Bar'}
		
		resp = self.app.get(login_url, extra_environ=headers)
		self.assertEqual(self.app.get('/user/dashboard').status, 200)
		
		resp = self.app.get('/user/_logout').follow()
		self.assertEqual(self.app.get('/user/dashboard').status, 302)

class TestShibbolethPlugin(unittest.TestCase):
	plugin = None

	def setUp(self, *args, **kwargs):
		self.plugin = create_plugin(**kwargs)
    
	def test_plugin_field_names(self):
		self.assertNotEqual(self.plugin, None)
		self.assertEqual(self.plugin.session, SESSION_FIELD)
		self.assertEqual(self.plugin.mail, MAIL_FIELD)
		self.assertEqual(self.plugin.name, NAME_FIELD)

	def test_plugin_created(self):
		self.assertNotEqual(self.plugin, None)
		
	def test_shib_session(self):
		env_dict = {SESSION_FIELD:SESSION_FIELD_VAL, MAIL_FIELD:u'foo@bar.com', NAME_FIELD:u'Foo Bar', AUTH_FIELD:SHIBBOLETH}
		self.assertEqual(self.plugin.is_shib_session(env_dict), True)
		
		env_dict = {SESSION_FIELD:SESSION_FIELD_VAL, MAIL_FIELD:u'foo@bar.com', NAME_FIELD:u'Foo Bar', AUTH_FIELD:'FooBarAuth'}
		self.assertEqual(self.plugin.is_shib_session(env_dict), False)

	def test_identify_without_shib_session(self):
		env = dict(PATH_INFO='/user/shiblogin')
		identity = self.plugin.identify(env)

		self.assertEqual(identity, {})

	def test_create_user(self):
		import re
		user_dict = {MAIL_FIELD:u'foo@bar.com', NAME_FIELD:u'Foo Bar', AUTH_FIELD:SHIBBOLETH}
		username = re.sub('[.@]', '_', user_dict[MAIL_FIELD])
		user = self.plugin._get_or_create_user(user_dict)

		self.assertNotEqual(user, {})
		self.assertEqual(user.openid, user_dict[MAIL_FIELD])
		self.assertEqual(user.name, username)
		self.assertEqual(user.fullname, user_dict[NAME_FIELD])
		
	def test_get_or_create_user(self):
		import re
		user_dict = {MAIL_FIELD:u'newfoo@bar.com', NAME_FIELD:u'New Foo Bar', AUTH_FIELD:SHIBBOLETH}
		username = re.sub('[.@]', '_', user_dict[MAIL_FIELD])
		
		user = User(name = username,
					fullname = user_dict[NAME_FIELD],
					email = user_dict[MAIL_FIELD],
					openid = user_dict[MAIL_FIELD])
		
		Session.add(user)
		Session.commit()
		
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
										NAME_FIELD:u'Foo Bar',
										AUTH_FIELD:'shibboleth'})
		
		# Wrong authentication type
		identity_2 = self.plugin.identify({'PATH_INFO':login_url,
										SESSION_FIELD:SESSION_FIELD_VAL,
										MAIL_FIELD:u'foo@bar.com',
										NAME_FIELD:u'Foo Bar',
										AUTH_FIELD:'FooAuth'})
		
		# Missing name field
		identity_3 = self.plugin.identify({'PATH_INFO':login_url,
										SESSION_FIELD:SESSION_FIELD_VAL,
										MAIL_FIELD:u'foo@bar.com',
										AUTH_FIELD:SHIBBOLETH})
		
		# Missing mail field
		identity_4 = self.plugin.identify({'PATH_INFO':login_url,
										SESSION_FIELD:SESSION_FIELD_VAL,
										NAME_FIELD:u'Foo Bar',
										AUTH_FIELD:SHIBBOLETH})
		
		# Missing session field
		identity_5 = self.plugin.identify({'PATH_INFO':login_url,
										MAIL_FIELD:u'foo@bar.com',
										NAME_FIELD:u'Foo Bar',
										AUTH_FIELD:SHIBBOLETH})

		self.assertEqual(identity_1, {})
		self.assertEqual(identity_2, {})
		self.assertEqual(identity_3, {})
		self.assertEqual(identity_4, {})
		self.assertEqual(identity_5, {})
		
	def test_identity_with_valid_shib_session(self):
		mail_val = u'foo@bar.com'
		name_val = u'Foo Bar'
		
		identity = self.plugin.identify({'PATH_INFO':login_url,
										SESSION_FIELD:SESSION_FIELD_VAL,
										MAIL_FIELD:mail_val,
										NAME_FIELD:name_val,
										AUTH_FIELD:SHIBBOLETH})
		
		self.assertNotEqual(identity, {})
		self.assertEqual(identity['email'], mail_val)
		self.assertEqual(identity['login'], mail_val)
		self.assertEqual(identity['fullname'], mail_val)
		self.assertEqual(identity['password'], '')
		self.assertEqual(identity['repoze.who.plugins.openid.userid'], mail_val)
		
	def test_remember(self):
		self.assertEqual(self.plugin.remember({}, {}), None)
			
	def test_forget(self):
		self.assertEqual(self.plugin.forget({}, {}), None)
		
		
		
		
		

