#!/usr/bin/env python
import subprocess
import argparse
import logging
import pprint
import glob
import sys
import os

ignore = ['empty']

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

def listdir(path):
    """
    Return a list of files in the given path.
    Ignores filenames in the global "ingore".
    """
    
    for entry in glob.glob(os.sep.join([path, "*"])):
        filename = os.path.basename(entry)
        if filename not in ignore:
            yield entry

class Config(object):

    def __init__(self, workdir, repos_path):
        self.paths = {
            "repos": repos_path,
            "work": workdir,
            "watch": os.sep.join([workdir, "watch"]),
            "done": os.sep.join([workdir, "done"]),
            "run": os.sep.join([workdir, "running"]),
            "process": os.sep.join([workdir, "processing"]),
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
        logging.error(err)

    return (out, err)

def check_watchfolder(conf):
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
            result_fn = "%s_%s" % (suitename, postfix)
            result_path = os.sep.join([conf.run_dir, "%s.json" % result_fn])
            out, err = bprun(conf, suite_path, result_path)

def main(args):
  
    logging.basicConfig(
        format="[%(filename)s:%(lineno)s %(funcName)17s ] %(message)s",
        level=logging.DEBUG
    )

    workdir = expand_path(args.workdir)
    repos_path = expand_path(args.repos)

    conf = Config(workdir, repos_path)
    if args.task == "watch":
        check_watchfolder(conf)
    else:
        pass

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
        choices=["watch", "running"]
    )
    args = parser.parse_args()
    main(args)
