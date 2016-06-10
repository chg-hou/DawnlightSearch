from distutils.core import setup

setup(
    name='DawnlightSearch',
    version='0.1',
    packages=['', 'DB_Builder', 'MFT_parser', 'QueryWorker', 'UI_delegate'],
    package_dir={'': 'DawnlightSearch'},
    url='https://github.com/chg-hou/DawnlightSearch',
    license='GPL2',
    author='chg-hou',
    author_email='chg.hou@gmail.com',
    description='A Linux version of Everything Search Engine.'
)
