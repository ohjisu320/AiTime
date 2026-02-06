# Makefile
# 사용:
#   make <svc> <action>
# 예:
#   make cmn start
#   make fe up
#   make be down
#   make ai1 dlog   # => docker logs -f <ai1 compose의 첫 컨테이너>
#
# action:
#   start : docker-compose up -d --build
#   up    : docker-compose up -d
#   down  : docker-compose down
#   dlog  : docker logs -f <container>

DC := docker-compose

# 서비스별 compose 파일 매핑
CMN_FILE       := docker-compose.yml
FE_FILE        := docker-compose.frontend.yml
BE_FILE        := docker-compose.backend.yml
AI1_FILE       := docker-compose.ai_task1.yml
AI2_FILE       := docker-compose.ai_task2.yml
AI3_FILE       := docker-compose.ai_task3.yml
AI4_FILE       := docker-compose.ai_task4.yml
LIVEKIT_FILE   := docker-compose.livekit.yml
SCREENING_FILE := docker-compose.screening.yml

# "make ai1 start" 형태에서 start/up/down/dlog를 더미 타겟으로 흡수
.PHONY: start up down dlog
start up down dlog: ; @:

# 서비스 타겟
.PHONY: cmn fe be ai1 ai2 ai3 ai4 livekit screening

cmn:       ; @$(MAKE) _run FILE="$(CMN_FILE)"       ACTION="$(filter-out $@,$(MAKECMDGOALS))"
fe:        ; @$(MAKE) _run FILE="$(FE_FILE)"        ACTION="$(filter-out $@,$(MAKECMDGOALS))"
be:        ; @$(MAKE) _run FILE="$(BE_FILE)"        ACTION="$(filter-out $@,$(MAKECMDGOALS))"
ai1:       ; @$(MAKE) _run FILE="$(AI1_FILE)"       ACTION="$(filter-out $@,$(MAKECMDGOALS))"
ai2:       ; @$(MAKE) _run FILE="$(AI2_FILE)"       ACTION="$(filter-out $@,$(MAKECMDGOALS))"
ai3:       ; @$(MAKE) _run FILE="$(AI3_FILE)"       ACTION="$(filter-out $@,$(MAKECMDGOALS))"
ai4:       ; @$(MAKE) _run FILE="$(AI4_FILE)"       ACTION="$(filter-out $@,$(MAKECMDGOALS))"
livekit:   ; @$(MAKE) _run FILE="$(LIVEKIT_FILE)"   ACTION="$(filter-out $@,$(MAKECMDGOALS))"
screening: ; @$(MAKE) _run FILE="$(SCREENING_FILE)" ACTION="$(filter-out $@,$(MAKECMDGOALS))"

.PHONY: _run
_run:
	@if [ -z "$(ACTION)" ]; then \
		echo "Usage: make <svc> <action>"; \
		echo "  svc    : cmn fe be ai1 ai2 ai3 ai4 livekit screening"; \
		echo "  action : start | up | down | dlog"; \
		exit 1; \
	fi

	@if [ "$(ACTION)" = "start" ]; then \
		$(DC) -f "$(FILE)" up -d --build; \
	elif [ "$(ACTION)" = "up" ]; then \
		$(DC) -f "$(FILE)" up -d; \
	elif [ "$(ACTION)" = "down" ]; then \
		$(DC) -f "$(FILE)" down; \
	elif [ "$(ACTION)" = "dlog" ]; then \
		CID="$$( $(DC) -f "$(FILE)" ps -q | head -n 1 )"; \
		if [ -z "$$CID" ]; then \
			echo "No running container found for compose file: $(FILE)"; \
			echo "먼저 'make <svc> up' 또는 'make <svc> start' 로 올려줘."; \
			exit 1; \
		fi; \
		NAME="$$( docker ps --format '{{.Names}}' --filter "id=$$CID" | head -n 1 )"; \
		if [ -z "$$NAME" ]; then \
			echo "Container is not running (or name not found): $$CID"; \
			exit 1; \
		fi; \
		echo "docker logs -f $$NAME"; \
		docker logs -f "$$NAME"; \
	else \
		echo "Unknown action: $(ACTION) (use start|up|down|dlog)"; \
		exit 1; \
	fi

