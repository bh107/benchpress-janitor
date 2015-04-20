all: clean_watch clean_running clean_graphing clean_done

clean_watch:
	@find workdir/watch
	@echo "About to remove files in watch-dir"
	rm -rI workdir/watch/*

clean_running:
	@find workdir/running
	@echo "About to remove files in running-dir"
	rm -rI workdir/running/*

clean_graphing:
	@find workdir/graphing
	@echo "About to remove files in graphing-dir"
	rm -rI workdir/graphing/*

clean_done:
	@find workdir/done
	@echo "About to remove files in done-dir"
	rm -rI workdir/done/*
