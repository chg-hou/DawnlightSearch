SHELL := /bin/bash

default:
	lsblk --version
	@type lsblk
	cd src ;\
	export QT_SELECT=qt5 ;\
	qmake -qt=qt5 CONFIG+=release  DawnlightSearch.pro ;\
	make ;\
	make clean ;\
	cd ..

	
install_ubuntu_dep:
	sudo apt install qt5-qmake kio-dev libsqlite3-dev util-linux -y
	
	
install:
	cd src ;\
	install -D  dawnlightsearch /opt/dawnlightsearch/dawnlightsearch ;\
	install -D  ui/icon/main.png /opt/dawnlightsearch/dawnlightsearch.png ;\
	install -D  dawnlightsearch_make_install.desktop /usr/share/applications/dawnlightsearch.desktop ;\
	cd ..
	
install_to_user:
	cd src ;\
	install -D  dawnlightsearch  ${HOME}/.local/bin/dawnlightsearch/dawnlightsearch ;\
	install -D  ui/icon/main.png ${HOME}/.local/bin/dawnlightsearch/dawnlightsearch.png ;\
	install -D  dawnlightsearch_make_install.desktop ${HOME}/.local/share/applications/dawnlightsearch.desktop ;\
	python -c "import os;a=os.environ['HOME'];f=open(a+'/.local/share/applications/dawnlightsearch.desktop','r+');a=f.read().replace('/opt/',a+'/.local/bin/');f.seek(0);f.write(a);f.close();" ;\
	cd ..
	
uninstall:
	rm ${HOME}/.local/bin/dawnlightsearch/dawnlightsearch ;\
	rm ${HOME}/.local/bin/dawnlightsearch/dawnlightsearch.png ;\
	rmdir ${HOME}/.local/bin/dawnlightsearch ;\
	rm ${HOME}/.local/share/applications/dawnlightsearch.desktop;\
	rm /opt/dawnlightsearch/dawnlightsearch ;\
	rm /opt/dawnlightsearch/dawnlightsearch.png ;\
	rmdir /opt/dawnlightsearch/ ;\
	rm /usr/share/applications/dawnlightsearch.desktop 
