# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = '0.2'

setup(
	name='ckanext-repoze-who-shibboleth',
	version=version,
	description="",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author=u'Harri Palojärvi',
	author_email='harri.palojarvi@nomovok.com',
	url='',
	license='',
	packages=find_packages(exclude=['ez_setup', 'tests']),
	namespace_packages=['ckanext', 'ckanext.repoze', 'ckanext.repoze.who', 'ckanext.repoze.who.shibboleth'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[],
	setup_requires=['nose>=1.0', 'coverage'],
	tests_require=['nose'],
	entry_points=\
	"""
	[ckan.plugins]
	# Add plugins here, eg
	shibboleth=ckanext.repoze.who.shibboleth.extension:CkanShibbolethPlugin
	""",

)
