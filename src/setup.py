
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

mft_c_parser_module = Extension('mft_c_parser_module',
                                sources=['DawnlightSearch/MFT_parser/mft_c_parser_module.cpp'],
                                libraries=["sqlite3"],
                                extra_compile_args=['-std=c++11']
                                )

setup(
    name='DawnlightSearch',
    version='0.1.0.1',
    packages=['DawnlightSearch'],
    package_dir={'DawnlightSearch': 'DawnlightSearch'},
    url='https://github.com/chg-hou/DawnlightSearch',
    license='GPL2',
    author='chg-hou',
    author_email='chg.hou@gmail.com',
    description='A Linux version of Everything Search Engine.',

    package_data={'DawnlightSearch': ['*.desktop',
                                      'ui/icon/*.png',
                                      '*.ui',
                                      'DB_Builder/*.py',
                                      'MFT_parser/*.py',
                                      'QueryWorker/*.py',
                                      'UI_delegate/*.py']},
    install_requires=['PyQt5'],
    data_files=[('share/applications',  ['DawnlightSearch/DawnlightSearch.desktop']),
                ('share/pixmaps',       ['DawnlightSearch/ui/icon/DawnlightSearch.png'])],
    ext_package='DawnlightSearch.MFT_parser',
    ext_modules=[mft_c_parser_module]
)


# depedence: PyQt5          python3-pyqt5
# xdg-utils
# python3-gi


