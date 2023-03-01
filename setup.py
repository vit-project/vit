import re
from setuptools import setup
from os import path

DEFAULT_BRANCH = "2.x"
BASE_GITHUB_URL = "https://github.com/vit-project/vit/blob"

MARKUP_LINK_REGEX = r"\[([^]]+)\]\(([\w]+\.md)\)"
FILE_DIR = path.dirname(path.abspath(path.realpath(__file__)))

with open(path.join(FILE_DIR, 'README.md')) as f:
    readme_contents = f.read()
    markup_link_substitution = '[\\1](%s/%s/\\2)' % (BASE_GITHUB_URL, DEFAULT_BRANCH)
    README = re.sub(MARKUP_LINK_REGEX, markup_link_substitution, readme_contents, flags=re.MULTILINE)

with open(path.join(FILE_DIR, 'requirements.txt')) as f:
    INSTALL_PACKAGES = f.read().splitlines()

with open(path.join(FILE_DIR, 'vit', 'version.py')) as f:
    VERSION = re.match(r"^VIT = '([\w\.]+)'$", f.read().strip())[1]

setup(
    name='vit',
    packages=['vit', 'vit.config', 'vit.formatter', 'vit.keybinding', 'vit.theme'],
    description="Visual Interactive Taskwarrior full-screen terminal interface",
    long_description=README,
    long_description_content_type='text/markdown',
    install_requires=INSTALL_PACKAGES,
    version=VERSION,
    url='https://github.com/vit-project/vit',
    author='Chad Phillips',
    author_email='chad@apartmentlines.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Programming Language :: Python',
        'Natural Language :: English',
        'Topic :: Text Processing :: General',
    ],
    keywords=[
        'taskwarrior',
        'console',
        'tui',
        'text-user-interface',
    ],
    tests_require=[
    ],
    entry_points = {
        'console_scripts': [
            'vit=vit.command_line:main',
        ],
    },
    include_package_data=True,
    python_requires='>=3.7',
    zip_safe=False
)
