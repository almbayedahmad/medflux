.PHONY: scaffold validate docgen hooks-install validate-strict

STAGE ?=
STAGE_NAME ?=
PHASE ?=
EVENT ?= update
CHANGELOG ?= $(STAGE)/CHANGELOG.md

scaffold:
	python codegen/stage_scaffold.py $(MANIFEST)

validate:
	python agent/agents_tasks/validation_op/standards_validator.py --standards-dir agent/agents_rules --stage-root $(STAGE)

doc-update:
	python agent/agents_tasks/change_op/auto_documentation_update.py --stage $(STAGE) --event $(EVENT) --stage-name $(STAGE_NAME) --phase $(PHASE) --changelog $(CHANGELOG) --main-readme main_documantion/main_readme.md --main-changelog main_documantion/main_changelog.md --current-stage main_documantion/main_current_development_stage.md

docgen:
	python tools/docgen/auto_doc_update.py

hooks-install:
	install -m 0755 tools/hooks/post-commit .git/hooks/post-commit || cp tools/hooks/post-commit .git/hooks/post-commit
	install -m 0755 tools/git_hooks/commit-msg .git/hooks/commit-msg || cp tools/git_hooks/commit-msg .git/hooks/commit-msg
	git config commit.template .gitmessage || true
