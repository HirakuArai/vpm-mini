compose-build:
	@if [ -f compose.yaml ]; then \
		docker compose build; \
	else \
		echo "compose.yaml not found; will be added in S2. Skipping build."; \
	fi

compose-up:
	docker compose up -d --wait

compose-down:
	docker compose down -v

compose-logs:
	docker compose logs --no-color --tail=200

# Claude Code template generator
CC_TMPL = ops/claude_templates/standard_pr.md.tmpl

cc:
	@python3 -c "import os,sys; \
	tmpl=open('$(CC_TMPL)','r',encoding='utf-8').read(); \
	vars={ \
	 'N': os.environ.get('STEP','?'), \
	 'TITLE': os.environ.get('TITLE','(no title)'), \
	 'SLUG': os.environ.get('SLUG','slug-missing'), \
	 'FILES': os.environ.get('FILES','- Files to be changed'), \
	 'FILES_FLAT': ' '.join([l.strip(' -') for l in os.environ.get('FILES','').splitlines() if l.strip()]), \
	 'DOD_TEXT': os.environ.get('DOD','CI green / Auto-merge / MERGED / snapshot+tag') \
	}; \
	for k,v in vars.items(): tmpl = tmpl.replace(f'<{k}>', v); \
	print(tmpl)"
.PHONY: hello-url hello-health test phase0-sanity
hello-url:
	@kubectl -n hyper-swarm get ksvc hello-ai -o jsonpath='{.status.url}{"\n"}'
hello-health:
	@URL=$$(kubectl -n hyper-swarm get ksvc hello-ai -o jsonpath='{.status.url}{"\n"}'); \
	curl -s -H "Host: hello-ai.hyper-swarm.127.0.0.1.sslip.io" http://127.0.0.1:8080/healthz

.PHONY: test phase0-sanity
phase0-sanity:
	python scripts/phase0_sanity/playground.py
test:
	pytest -q

verify:
	@PR=$${PR:?}; SLUG=$${SLUG:?}; set -e; \
	echo "== PR 状態 =="; \
	gh pr view $$PR --json state,mergedAt,mergeCommit,url \
	  -q '"state=" + .state + " mergedAt=" + (.mergedAt//"") + " mergeCommit=" + (.mergeCommit.abbreviatedOid//"") + " url=" + .url'; \
	STATE=$$(gh pr view $$PR --json state -q .state); \
	test "$$STATE" = "MERGED"; \
	echo "== snapshot on origin/main =="; \
	git fetch origin main >/dev/null; \
	git cat-file -e origin/main:reports/snap_$${SLUG}.md \
	  && echo "OK: reports/snap_$${SLUG}.md" \
	  || (echo "MISSING: reports/snap_$${SLUG}.md"; exit 1); \
	echo "== tag on remote =="; \
	git ls-remote --tags origin | grep -q "refs/tags/$${SLUG}" \
	  && echo "OK: tag $${SLUG}" \
	  || (echo "MISSING: tag $${SLUG}"; exit 1)

# === Trial Mode ===
trial-daily:
	@chmod +x tools/vpm_trial_status.sh tools/vpm_daily_capture.sh 2>/dev/null || true
	@echo "== Trial Daily Status =="
	@tools/vpm_trial_status.sh || true
	@echo "== Capture Evidence =="
	@tools/vpm_daily_capture.sh
