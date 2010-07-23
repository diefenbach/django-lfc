from setuptools import setup, find_packages
import os

version = '1.0b5'

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()

setup(name='django-lfc',
      version=version,
      description='A CMS based on Django.',
      long_description=README,
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Django',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
      ],
      keywords='django lfc cms',
      author='Kai Diefenbach',
      author_email='kai.diefenbach@iqpp.de',
      url='http://www.iqpp.de',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        'django-contact-form',
        'django-pagination == 1.0.7',
        'django-permissions >0.9,<=1.0',
        'django-portlets >0.9,<=1.0',
        'django-workflows >0.9,<=1.0',
        'tagging == 0.5',
        'feedparser',
        'lfc_theme >0.9,<=1.0',
      ],
      )
