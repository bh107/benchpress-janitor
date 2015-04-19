Modify ``config.sh`` and ``daily.sh`` to suite needs / system.
Then do a `crontab -e` along the lines of::

  SHELL=/bin/bash
  
  # Push suites into the janitors watch-folder
  0 4 * * 1 source $HOME/.bash_profile; cd /home/safl/perftest && ./daily.sh

  # Ask the janitor to do a watch & run
  */30 * * * 1 source $HOME/.bash_profile; cd $HOME/perftest && ./check.sh

Then it should start rolling in those numbers...
