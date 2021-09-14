# -*- coding: utf-8; mode: makefile-gmake -*-
# SPDX-License-Identifier: AGPL-3.0-or-later

.DEFAULT_GOAL=help
export MTOOLS=./manage

include utils/makefile.include

all: clean install

PHONY += help

help:
	@./manage --help
	@echo '----'
	@echo 'run            - run developer instance'
	@echo 'install        - developer install of searx into virtualenv'
	@echo 'uninstall      - uninstall developer installation'
	@echo 'clean          - clean up working tree'
	@echo 'search.checker - check search engines'
	@echo 'test           - run shell & CI tests'
	@echo 'test.shell     - test shell scripts'
	@echo 'ci.test        - run CI tests'


PHONY += run
run:  install
	$(Q) ( \
	sleep 2 ; \
	xdg-open http://127.0.0.1:8888/ ; \
	) &
	SEARX_DEBUG=1 ./manage pyenv.cmd python -m searx.webapp

PHONY += install uninstall
install uninstall:
	$(Q)./manage pyenv.$@

PHONY += clean
clean: py.clean docs.clean node.clean test.clean
	$(Q)./manage build_msg CLEAN  "common files"
	$(Q)find . -name '*.orig' -exec rm -f {} +
	$(Q)find . -name '*.rej' -exec rm -f {} +
	$(Q)find . -name '*~' -exec rm -f {} +
	$(Q)find . -name '*.bak' -exec rm -f {} +

lxc.clean:
	$(Q)rm -rf lxc-env

PHONY += search.checker search.checker.%
search.checker: install
	$(Q)./manage pyenv.cmd searx-checker -v

search.checker.%: install
	$(Q)./manage pyenv.cmd searx-checker -v "$(subst _, ,$(patsubst search.checker.%,%,$@))"

PHONY += test ci.test test.shell
ci.test: test.yamllint test.pep8 test.pylint test.unit test.robot
test:    test.yamllint test.pep8 test.pylint test.unit test.robot test.shell
test.shell:
	$(Q)shellcheck -x -s dash \
		dockerfiles/docker-entrypoint.sh
	$(Q)shellcheck -x -s bash \
		utils/brand.env \
		$(MTOOLS) \
		utils/lib.sh \
		utils/lib_install.sh \
		utils/lib_static.sh \
	        utils/filtron.sh \
	        utils/searx.sh \
	        utils/morty.sh \
	        utils/lxc.sh \
	        utils/lxc-searx.env \
	        .config.sh
	$(Q)$(MTOOLS) build_msg TEST "$@ OK"


# wrap ./manage script

MANAGE += buildenv
MANAGE += weblate.translations.commit weblate.push.translations
MANAGE += data.all data.languages data.useragents data.osm_keys_tags
MANAGE += docs.html docs.live docs.gh-pages docs.prebuild docs.clean
MANAGE += docker.build docker.push docker.buildx
MANAGE += gecko.driver
MANAGE += node.env node.clean
MANAGE += py.build py.clean
MANAGE += pyenv pyenv.install pyenv.uninstall
MANAGE += pypi.upload pypi.upload.test
MANAGE += test.yamllint test.pylint test.pep8 test.unit test.coverage test.robot test.clean
MANAGE += themes.all themes.oscar themes.simple pygments.less
MANAGE += static.build.commit static.build.drop static.build.restore

PHONY += $(MANAGE)

$(MANAGE):
	$(Q)$(MTOOLS) $@


# deprecated

PHONY += docs docs-clean docs-live docker themes

docs: docs.html
	$(Q)./manage build_msg WARN $@ is deprecated use docs.html

docs-clean: docs.clean
	$(Q)./manage build_msg WARN $@ is deprecated use docs.clean

docs-live: docs.live
	$(Q)./manage build_msg WARN $@ is deprecated use docs.live

docker:  docker.build
	$(Q)./manage build_msg WARN $@ is deprecated use docker.build

themes: themes.all
	$(Q)./manage build_msg WARN $@ is deprecated use themes.all
