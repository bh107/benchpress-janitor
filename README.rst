Modify ``config.sh`` and ``daily.sh`` to suite needs / system.
Then do a `crontab -e` along the lines of::

  SHELL=/bin/bash
  
  # Push suites into the janitors watch-folder
  55 3 * * * source $HOME/.bash_profile; cd $HOME/perftest && ./daily_job.sh
  
  # Ask the janitor to do a watch & run
  */30 * * * * source $HOME/.bash_profile; cd $HOME/perftest && ./check.sh

  # Last line cannot be empty!?

Then it should start rolling in those numbers...
