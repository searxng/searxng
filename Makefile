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
	@echo 'install        - developer install of SearxNG into virtualenv'
	@echo 'uninstall      - uninstall developer installation'
	@echo 'clean          - clean up working tree'
	@echo 'search.checker - check search engines'
	@echo 'test           - run shell & CI tests'
	@echo 'test.shell     - test shell scripts'
	@echo 'ci.test        - run CI tests'


PHONY += run
run:  install
	$(Q)./manage webapp.run

PHONY += install uninstall
install uninstall:
	$(Q)./manage pyenv.$@

PHONY += clean
clean: py.clean docs.clean node.clean nvm.clean test.clean
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
ci.test: test.yamllint test.black test.pyright test.pylint test.unit test.robot test.rst test.pybabel
test:    test.yamllint test.black test.pyright test.pylint test.unit test.robot test.rst test.shell
test.shell:
	$(Q)shellcheck -x -s dash \
		dockerfiles/docker-entrypoint.sh
	$(Q)shellcheck -x -s bash \
		utils/brand.env \
		$(MTOOLS) \
		utils/lib.sh \
		utils/lib_nvm.sh \
		utils/lib_static.sh \
		utils/lib_go.sh \
		utils/lib_redis.sh \
		utils/filtron.sh \
		utils/searx.sh \
		utils/searxng.sh \
		utils/morty.sh \
		utils/lxc.sh \
		utils/lxc-searxng.env
	$(Q)$(MTOOLS) build_msg TEST "$@ OK"


# wrap ./manage script

MANAGE += buildenv
MANAGE += weblate.translations.commit weblate.push.translations
MANAGE += data.all data.traits data.useragents
MANAGE += docs.html docs.live docs.gh-pages docs.prebuild docs.clean
MANAGE += docker.build docker.push docker.buildx
MANAGE += gecko.driver
MANAGE += node.env node.env.dev node.clean
MANAGE += py.build py.clean
MANAGE += pyenv pyenv.install pyenv.uninstall
MANAGE += pypi.upload pypi.upload.test
MANAGE += format.python
MANAGE += test.yamllint test.pylint test.pyright test.black test.pybabel test.unit test.coverage test.robot test.rst test.clean
MANAGE += themes.all themes.simple themes.simple.test pygments.less
MANAGE += static.build.commit static.build.drop static.build.restore
MANAGE += nvm.install nvm.clean nvm.status nvm.nodejs

PHONY += $(MANAGE)

$(MANAGE):
	$(Q)$(MTOOLS) $@

# short hands of selected targets

PHONY += docs docker themes

docs: docs.html
docker:  docker.build
themes: themes.all
