from setuptools import setup, find_packages
from cati_portal import __version__
from cati_portal import __author__
from cati_portal import __email__
from cati_portal import __license__


def readme():
    with open('README.txt') as f:
        return f.read()


def changes():
    with open('CHANGES.txt') as f:
        return f.read()

setup(
    name='cati_portal',
    version=__version__,
    author=__author__,
    author_email=__email__,
    description='CATI Portal',
    long_description=readme() + '\n\n' + changes(),
    license=__license__,
    url='https://github.com/sapetnioc/cati_portal',
    classifiers=[
        'Programming Language :: Python',
        "Programming Language :: Python :: 3",
        'Framework :: Flask',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    keywords='web flask',
    packages=find_packages(),
    scripts=[
        'cati_portal_ctl',
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask >= 1.0',
        'flask-login',
        'flask-wtf',
        'psycopg2-binary >= 2.7',
        'click >= 5.0',
        'gunicorn',
    ],
    extras_require={
        'testing': [
            #'WebTest >= 1.3.1',  # py3 compat
            #'pytest',
            #'pytest-cov',
        ],
    },
)
