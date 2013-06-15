
PARTS = args.pl cmdline.pl cmds.pl color.pl curses.pl draw.pl env.pl \
  exec.pl getch.pl misc.pl prompt.pl read.pl screen.pl

build: 
	@echo "adding vit.pl to vit"
	@cat vit.pl | grep -v ^require \
	  | sed "s/@BUILD@/`cat VERSION` built `date`/" \
	  | sed "s/@VERSION@/`cat VERSION` (`date +%Y%m%d`)/" \
	  > vit
	@for f in $(PARTS); do \
	  echo "adding $$f to vit"; \
	  echo "##################################################################" >> vit; \
	  echo "## $$f..." >> vit; \
	  grep -v ^return $$f >> vit; \
	done
	chmod 755 vit

install:
	sudo mkdir -p /usr/local/bin
	sudo cp vit /usr/local/bin/vit
	sudo mkdir -p /usr/local/etc
	sudo cp commands /usr/local/etc/vit-commands

testing:
	@make -f .makefile testing

release:
	@make -f .makefile release

diffs:
	@make -f .makefile diffs

ci:
	@make -f .makefile ci

push:
	@make -f .makefile push

