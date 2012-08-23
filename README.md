ckanext-shibboleth
==================

Shibboleth authentication plugin for CKAN

Install
-------
  pip install -e git+git://github.com/harripal/ckanext-shibboleth.git#egg=ckanext-shibboleth
	
Nosetests
---------
	$ cd ~/pyenv/src/ckan
	$ nosetests --ckan ../ckanext-shibboleth/tests
	
Plugin configuration
--------------------
pyenv/src/ckan/who.ini

	[plugin:shibboleth]
	use = ckanext.repoze.who.shibboleth.plugin:make_identification_plugin
	session = Shib-Session-ID
	mail = mail
	name = cn

	[general]
	request_classifier = repoze.who.classifiers:default_request_classifier
	challenge_decider = repoze.who.plugins.openid.classifiers:openid_challenge_decider

	[identifiers]
	plugins =
		friendlyform;browser
		shibboleth
		openid
		auth_tkt

	[authenticators]
	plugins = 
		ckan.lib.authenticator:OpenIDAuthenticator
		ckan.lib.authenticator:UsernamePasswordAuthenticator

	[challengers]
	plugins =
		openid
		friendlyform;browser
