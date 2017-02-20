import os

from setuptools import setup, find_packages

requires = [
    'pyramid',
    'pyramid_jinja2',
    'pyramid_debugtoolbar',
    'pyramid_tm',
    'SQLAlchemy',
    'alembic',
    'transaction',
    'zope.sqlalchemy',
    'waitress',
    ]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest',  # includes virtualenv
    'pytest-cov',
    ]

postgresql_requires = [
    'psycopg2',
    ]

setup(name='cati_manager',
      version='0.0',
      description='cati_manager',
      long_description='',
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      extras_require={
          'testing': tests_require,
          'postgresql': postgresql_requires,
      },
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = cati_manager:main
      [console_scripts]
      initialize_cati_manager_db = cati_manager.scripts.initializedb:main
      """,
      )
