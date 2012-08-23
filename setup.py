from setuptools import setup, find_packages
import sys, os

version = '0.2'

setup(
	name='ckanext-repoze-who-shibboleth',
	version=version,
	description="",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='',
	author_email='',
	url='',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext',
						'ckanext.repoze',
						'ckanext.repoze.who',
						'ckanext.repoze.who.shibboleth'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[],
	entry_points=\
	"""
        [ckan.plugins]
	# Add plugins here, eg
	shibboleth2=ckanext.repoze.who.shibboleth.extension:CkanShibbolethPlugin
	""",
)
