VERSION = $(shell cat VERSION)
PYTHON = $(shell pyexe.py)
INNO = $(shell innoexe.py)
BASENAME = gmailtray_$(VERSION)
INSTALLER_BASE = $(BASENAME)_setup
INSTALLER = $(INSTALLER_BASE).exe 
EXTRA = README.html *.ico *.css LICENSE.txt ChangeLog
ARCHDIR = $(subst _,-,$(BASENAME))
ARCHIVE = $(ARCHDIR).tar.bz2
SRCFILES = $(shell $(PYTHON) srcfiles.py)

all:
	@echo "Done :) (you probably want to run 'make installer')"

installer: $(INSTALLER)

$(INSTALLER): dist setup.iss version.iss
	$(INNO) setup.iss

dist: gmailtray.py setup.py version.py $(EXTRA)
	$(PYTHON) setup.py py2exe
	cp -f $(EXTRA) $@

README.html: README.txt
	sed -e "s/_VERSION_/$(VERSION)/" $< | rst2html.py --stylesheet=style.css > $@

srcdist: $(ARCHIVE)

$(ARCHIVE): $(SRCFILES)
	mkdir $(ARCHDIR)
	cp $(SRCFILES) $(ARCHDIR)
	tar -cjf $(ARCHIVE) $(ARCHDIR)
	rm -fr $(ARCHDIR)

clean:
	rm -f version.py version.iss
	rm -fr dist build
	rm -f *.pyc
	rm -f README.html
	rm -f $(INSTALLER)

version.iss: VERSION
	echo "AppVerName = GmailTray version $(VERSION)" > $@
	echo "OutputBaseFileName = $(INSTALLER_BASE)" >> $@

version.py: VERSION
	echo "VERSION = \"$(VERSION)\"" > $@

fresh: clean all

.PHONY: all installer clean fresh
