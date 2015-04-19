
Do a `crontab -e` along the lines of::

  # Push suites into the janitors watch-folder
  0 4 * * 1 cd /home/safl/perftest && ./daily_job.sh
  
  # Ask the janitor to do a watch & run
  */15 * * * 1 cd /home/safl/perftest && ./check.sh

