.PHONY: test_task_3_1 demo_task_3_1 stop_agency_a start_agency_a stop_agency_b start_agency_b clean_demo

# Tests for Task 3.1: Perception and Actuation
test_task_3_1:
	cd option3_perception_actuation && pytest

test_all: test_task_3_1

# Demo Task 3.1: Perception and Actuation
demo_task_3_1:
	rm -f data/listener.db option3_perception_actuation/data/listener.db
	@chmod +x scripts/start_demo_task_3_1.sh
	@./scripts/start_demo_task_3_1.sh

clean_demo:
	pkill -9 -f "uvicorn agencies" || true
	pkill -9 -f "listener_demo" || true
	@rm -f /tmp/agency_*.pid
	@rm -f data/listener.db option3_perception_actuation/data/listener.db
	@find option3_perception_actuation -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find option3_perception_actuation -type f -name "*.pyc" -delete 2>/dev/null || true

# Targets to manage Agency A (for manual testing during demo)
AGENCY_A_PID_FILE := /tmp/agency_a.pid
AGENCY_B_PID_FILE := /tmp/agency_b.pid

stop_agency_a:
	@if [ -f "$(AGENCY_A_PID_FILE)" ]; then \
		kill $$(cat $(AGENCY_A_PID_FILE)) 2>/dev/null || true; \
		rm -f $(AGENCY_A_PID_FILE); \
		echo "Agency A stopped"; \
	else \
		pkill -f "uvicorn agencies.agency_a" || true; \
		echo "Agency A stopped"; \
	fi

start_agency_a:
	@cd option3_perception_actuation && \
	uvicorn agencies.agency_a:app --host 127.0.0.1 --port 8001 > /tmp/agency_a.log 2>&1 & \
	echo $$! > $(AGENCY_A_PID_FILE); \
	sleep 1; \
	echo "Agency A started (PID: $$(cat $(AGENCY_A_PID_FILE)))"

stop_agency_b:
	@if [ -f "$(AGENCY_B_PID_FILE)" ]; then \
		kill $$(cat $(AGENCY_B_PID_FILE)) 2>/dev/null || true; \
		rm -f $(AGENCY_B_PID_FILE); \
		echo "Agency B stopped"; \
	else \
		pkill -f "uvicorn agencies.agency_b" || true; \
		echo "Agency B stopped"; \
	fi

start_agency_b:
	@cd option3_perception_actuation && \
	uvicorn agencies.agency_b:app --host 127.0.0.1 --port 8002 > /tmp/agency_b.log 2>&1 & \
	echo $$! > $(AGENCY_B_PID_FILE); \
	sleep 1; \
	echo "Agency B started (PID: $$(cat $(AGENCY_B_PID_FILE)))"
