
default:
	lsblk --version ; \
	if [ $? -ne 0 ]; then \
		echo "lsblk command, which is part of the util-linux, not found."; \
		exit 1; \
	else \
		echo "lsblk found."; \
	fi ;\
	cd src ;\
	export QT_SELECT=qt5 ;\
	qmake -qt=qt5 CONFIG+=release  DawnlightSearch.pro ;\
	make ;\
	make clean ;\
	cd ..

	
install_ubuntu_dep:
	sudo apt install qt5-qmake kio-dev -y
	
	
install:
	cd src ;\
	install -D  dawnlightsearch /opt/dawnlightsearch/dawnlightsearch ;\
	install -D  ui/icon/main.png /opt/dawnlightsearch/dawnlightsearch.png ;\
	install -D  dawnlightsearch_make_install.desktop /usr/share/applications/dawnlightsearch.desktop ;\
	cd ..
	
uninstall:
	rm /opt/dawnlightsearch/dawnlightsearch ;\
	rm /opt/dawnlightsearch/dawnlightsearch.png ;\
	rmdir /opt/dawnlightsearch/ ;\
	rm /usr/share/applications/dawnlightsearch.desktop 
