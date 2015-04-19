#!/usr/bin/env python
import argparse
import pprint
import glob
import sys
import os

ignore = ['empty']

def expand_path(path):
    """Expand stuff like "~" and $HOME ..."""
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
        for path in self.paths:
            setattr(self, "%s_%s" % (path, "dir"), self.paths[path])

    def __str__(self):
        return pprint.pformat(self.paths)

def check_watchfolder(conf):
    """
    Check if there is anything in the watch-folder and
    start new benchpress runs if there is anything there.
    """

    jobs = []                       # Find an specify "jobs"
    for wfile in listdir(conf.watch_dir):
        suitename = os.path.basename(wfile)

        postfixes = []              # Find specified postfixes
        for line in open(wfile):
            postfixes.append(line.strip())

        if not postfixes:           # Default postfix for output filename
            postfixes.append("01")

        for postfix in postfixes:   # Add the jobs
            jobs.append((suitename, "%s_%s" % (suitename, postfix)))

        # Remove the watch-file
        os.remove(wfile)

    # TODO: execute the bp-run
    print jobs

def main(args):
    
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
