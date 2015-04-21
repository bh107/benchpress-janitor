all: test_add test_watch test_run test_postprocess view_log

test_add:
	@echo "** Adding a job"
	echo "01" > workdir/watch/perftest_mini
	echo "02" > workdir/watch/perftest_mini

test_watch:
	@echo "** Watching..."
	./janitor.py ~/bohrium watch

test_run:
	@echo "** Running..."
	./janitor.py ~/bohrium run

test_postprocess:
	@echo "** Running..."
	./janitor.py ~/bohrium postprocess

view_log:
	less +F janitor.log

clean: clean_watch clean_running clean_postprocessing clean_done

clean_watch:
	@echo "** About to delete the following"
	@find workdir/watch
	@echo "** About to delete the above"
	rm -rI workdir/watch/*

clean_running:
	@echo "** About to delete the following"
	@find workdir/running
	@echo "** About to delete the above"
	rm -rI workdir/running/*

clean_postprocessing:
	@echo "** About to delete the following"
	@find workdir/postprocessing
	@echo "** About to delete the above"
	rm -rI workdir/postprocessing/*

clean_done:
	@echo "** About to delete the following"
	@find workdir/done
	@echo "** About to delete the above"
	rm -rI workdir/done/*
