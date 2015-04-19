#!/usr/bin/env python
import subprocess
import argparse
import logging
import random
import pprint
import string
import json
import glob
import sys
import os

class Config(object):

    def __init__(self, workdir, repos_path):
        self.paths = {
            "repos": repos_path,
            "work": workdir,
            "watch": os.sep.join([workdir, "watch"]),
            "done": os.sep.join([workdir, "done"]),
            "run": os.sep.join([workdir, "running"]),
        }

        (suitesdir, suites) = find_suites()

        self.paths["suites"] = suitesdir
        self.suites = suites

        for path in self.paths:
            setattr(self, "%s_%s" % (path, "dir"), self.paths[path])

    def __str__(self):
        rep = "\n".join([
            "PATHS: %s" % pprint.pformat(self.paths),
            "SUITES: %s" % pprint.pformat(self.suites)
        ])
        
        return rep 

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """Credit: http://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python"""

    return ''.join(random.choice(chars) for _ in range(size))

def find_suites():
    """
    Return a dict of suitename and path, e.g.
    {"heat_equation": /home/safl/bechpress/suites/cpu/heat_equation.py"}
    """
    p = subprocess.Popen(
        ["bp-info", "--suites"],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )
    out, err = p.communicate()
    suitesdir = out.strip()
    if err:
        raise Exception("Error when trying to find suites-dir.")

    suites = {}
    for root, dirs, files in os.walk(suitesdir):
        for filename in files:
            if "__init__" in filename:
                continue
            if not filename.endswith(".py"):
                continue
            suitepath = os.sep.join([root, filename])
            suitename = os.path.splitext(filename)[0]
            suites[suitename] = suitepath
   
    return (suitesdir, suites)

def expand_path(path):
    """
    Expand stuff like "~" and $HOME...
    """
    expanded = os.path.abspath(os.path.expandvars(os.path.expanduser(path)))
    if not os.path.exists(expanded):
        raise Exception("Path %s|%s does exists." % (path, expanded))

    return expanded

def listdir(path, ignore=["empty"]):
    """
    Return a list of files in the given path.
    Ignores filenames in the "ignore".
    """
    
    for entry in glob.glob(os.sep.join([path, "*"])):
        filename = os.path.basename(entry)
        if filename not in ignore:
            yield entry

def bprun(conf, suite_path, result_path):
    """
    Execute the bp-run command for the given suite and output-postfix.
    """

    cmd = [
        "bp-run",
        conf.repos_dir,
        suite_path,
        "--output",
        result_path
        
    ]
    cmd_str = " ".join(cmd)
    logging.info("Running: `%s`" % cmd_str)

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    if err:
        logging.error("The command threw up the following error: [%s]" % err)

    return (out, err)

def check_watching(conf):
    """
    Check if there is anything in the watch-folder and
    start new benchpress runs if there is anything there.
    """

    for wfile in listdir(conf.watch_dir):   # Find files
        logging.info("Found %s" % wfile)
        suitename = os.path.basename(wfile)

        if suitename not in conf.suites:
            logging.error("Cannot find suite(%s), skipping" % suitename)
            continue

        postfixes = []                      # Find specified postfixes
        for line in open(wfile):
            postfixes.append(line.strip())

        os.remove(wfile)                    # Remove the watch-file
        logging.info("Removing %s" % wfile)
        
        if not postfixes:                   # Set one if none is found
            postfixes.append("01")

        for postfix in postfixes:           # Start bp-run for each
            suite_path = conf.suites[suitename]
            result_fn = "%s-%s" % (suitename, postfix)
            result_path = os.sep.join([conf.run_dir, "%s.json" % result_fn])

            if os.path.exists(result_path):
                logging.error(
                    "Skipping(%s), since it is already running." % result_fn
                )
                continue

            out, err = bprun(conf, suite_path, result_path)

def check_running(conf):
    """
    Check running jobs.
    """

    for rfile in listdir(conf.run_dir):
        result_path = os.path.abspath(rfile)    # Get the result path
        result_fn = os.path.basename(result_path)
        logging.info("Found %s" % result_path)
                                                # Get the suitename
        suite_abspath = json.load(open(result_path))["meta"]["suite"]
        suite_fn = os.path.basename(suite_abspath)
        suitename = os.path.splitext(suite_fn)[0]
        logging.info("It uses suite(%s)" % suitename)

        suite_path = conf.suites[suitename]     # Get the suite_path

        out, err = bprun(                       # Do the run
            conf,
            suite_path,
            result_path
        )

        if "Benchmark all finished" in out:     # Check the status
            logging.info("Run is done...")
            done_path = os.sep.join([conf.done_dir, result_fn])
            logging.info("done_path(%s)" % done_path)
            if os.path.exists(done_path):
                logging.info("Conflict, changing done_path.")
                postfix = id_generator()
                done_path = ".".join([
                    os.path.splitext(done_path)[0],
                    postfix,
                    "json"
                ])
                logging.info("Changed to: %s" % done_path)
                
            os.rename(result_path, done_path)# Move out of running

TASKS = {
    "watch":    check_watching,
    "run":      check_running
}

def main(args):
  
    logging.basicConfig(
        filename="janitor.log",
        format="[%(asctime)s %(filename)s:%(lineno)s %(funcName)17s ] %(message)s",
        level=logging.DEBUG
    )

    workdir = expand_path(args.workdir)
    repos_path = expand_path(args.repos)

    conf = Config(workdir, repos_path)
    TASKS[args.task](conf)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Janitor script.'
    )
    parser.add_argument(
        '--workdir',
        type=str,
        default='workdir',
        help="Path to the janitor workdir."
    )
    parser.add_argument(
        'repos',
        type=str,
        help="Path to the Bohrium repos."
    )
    parser.add_argument(
        'task',
        type=str,
        help="What do you want to do.",
        choices=[task for task in TASKS]
    )
    args = parser.parse_args()
    main(args)
