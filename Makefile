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
	 'DOD_TEXT': os.environ.get('DOD','CI green / Auto-merge / MERGED / snapshot+tag'), \
	}; \
	for k,v in vars.items(): tmpl = tmpl.replace(f'<{k}>', v); \
	print(tmpl)"