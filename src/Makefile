# https://github.com/matlink/gplaycli/blob/master/Makefile
SHELL := /bin/bash
PYTHON=`which python`
VERSION=0.1.1.1


all:
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"
	@echo "make pylupdate "
	@echo "make pyuic "
	

sdist:
	export PYTHONPATH=~/lib/python/:$PYTHONPATH
	python3 setup.py sdist

bdist:
	export PYTHONPATH=~/lib/python/:$PYTHONPATH
	python3 setup.py bdist

build_ext:
	export PYTHONPATH=~/lib/python/:$PYTHONPATH	
	python3 setup.py build_ext --inplace

bdist_deb:
	export PYTHONPATH=~/lib/python/:$PYTHONPATH
	DEBEMAIL=chg.hou@gmail.com
	DEBFULLNAME=Chenguang\ Hou
	# python3 setup.py --command-packages=stdeb.command sdist_dsc --sign-results bdist_deb
	python3 setup.py --command-packages=stdeb.command bdist_deb

sdist_deb:
	export PYTHONPATH=~/lib/python/:$PYTHONPATH
	DEBEMAIL=chg.hou@gmail.com
	DEBFULLNAME=Chenguang\ Hou
	# python3 setup.py --command-packages=stdeb.command sdist_dsc --sign-results bdist_deb
	python3 setup.py --command-packages=stdeb.command sdist_dsc

publish_deb_ppa:
	export PYTHONPATH=~/lib/python/:$PYTHONPATH
	DEBEMAIL=chg.hou@gmail.com
	DEBFULLNAME=Chenguang\ Hou
	# python3 setup.py --command-packages=stdeb.command sdist_dsc --sign-results bdist_deb
	python3 setup.py --command-packages=stdeb.command sdist_dsc --default-distribution xenial 

	# python3 setup.py --command-packages=stdeb.command sdist_dsc bdist_deb --default-distribution xenial 
deb_sign:
	cd deb_dist/dawnlightsearch-${VERSION}/;pwd;debuild -S
publish:
	python setup.py register -r pypi
	python setup.py sdist upload -r pypi

ppa_build_upload:
	make publish_deb_ppa
	make deb_sign
	cd deb_dist; dput -f ppa:chg-hou/dawnlightsearch dawnlightsearch_${VERSION}-1_source.changes

gitpush:
	git push origin master && git push github master

clean:
	$(PYTHON) setup.py clean
	rm -rf build/ MANIFEST dist GPlayCli.egg-info debian/{gplaycli,python-module-stampdir} debian/gplaycli.{debhelper.log,postinst.debhelper,prerm.debhelper,substvars} *.tar.gz* deb_dist
	find . -name '*.pyc' -delete

# pylupdate5 test1.py -ts zh_CN.ts
# https://kuanyui.github.io/2014/09/03/pyqt-i18n/
pylupdate:
     
	pylupdate5 translate.pro

pyuic:
	pyuic5 ./DawnlightSearch/Ui_mainwindow.ui -o ./DawnlightSearch/_Ui_mainwindow.py
	pyuic5 ./DawnlightSearch/Ui_edit_exclued_folder.ui -o ./DawnlightSearch/_Ui_edit_exclued_folder.py
	pyuic5 ./DawnlightSearch/Ui_advanced_setting_dialog.ui -o ./DawnlightSearch/_Ui_advanced_setting_dialog.py
