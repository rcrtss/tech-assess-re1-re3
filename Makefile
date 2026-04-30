.PHONY: test_task_3_1

test_task_3_1:
	cd option3_perception_actuation && pytest

test_all: test_task_3_1