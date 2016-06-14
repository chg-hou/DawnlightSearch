
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='DawnlightSearch',
    version='0.1',
    packages=['DawnlightSearch'],
    package_dir={'DawnlightSearch': 'DawnlightSearch'},
    url='https://github.com/chg-hou/DawnlightSearch',
    license='GPL2',
    author='chg-hou',
    author_email='chg.hou@gmail.com',
    description='A Linux version of Everything Search Engine.',

    package_data={'DawnlightSearch': ['*.desktop','ui/icon/*.png', 'MFT_parser/mft_cpp_parser','*.ui',
                                      'DB_Builder/*.py', 'MFT_parser/*.py','QueryWorker/*.py',
                                      'UI_delegate/*.py']},
    install_requires=['PyQt5'],
    data_files=[('share/applications',  ['DawnlightSearch/DawnlightSearch.desktop']),
                ('share/pixmaps',       ['DawnlightSearch/ui/icon/DawnlightSearch.png'])],

)


# depedence: PyQt5          python3-pyqt5
# xdg-utils
# python3-gi