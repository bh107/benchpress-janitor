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

def touch(file_path):
    logging.info(file_path)
    open(file_path, 'wa').close()

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

class Config(object):

    def __init__(self, workdir, repos_path):
        self.paths = {
            "repos": repos_path,
            "work": workdir,
            "watch": os.sep.join([workdir, "watch"]),
            "done": os.sep.join([workdir, "done"]),
            "run": os.sep.join([workdir, "running"]),
            "postprocess": os.sep.join([workdir, "postprocessing"]),
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

def bprun(conf, cwd, suite_path, result_path):
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
        stderr=subprocess.PIPE,
        cwd=cwd
    )
    out, err = p.communicate()
    if err:
        logging.error("The command threw up the following error: [%s]" % err)

    return (out, err)

def bpgrapher(conf, cwd, grapher, result_path, output_path):
    """
    Execute the bp-grapher command for the given result-file and output-file.
    """

    result_fn = os.path.basename(result_path)
    result_id = os.path.splitext(result_fn)[0]

    logging.info("Apply '%s' to '%s'" % (grapher, result_id))

    cmd = [
        "bp-grapher",
        result_path,
        "--type",
        grapher,
        "--output",
        output_path
    ]
    cmd_str = " ".join(cmd)
    logging.info("Running: `%s`" % cmd_str)
    
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd
    )
    out, err = p.communicate()
    if err:
        logging.error("The command threw up the following error: [%s]" % err)

    return (out, err)

def archive_container(conf, container_path):
    """Tars the given path and puts the archive inside."""

    (container_id, suitename, suite_path, result_path) = get_container_info(
        conf, container_path
    )

    archive_commands = [
        "tar -czf archive.tgz * --exclude=archive*",
        "zip archive.zip * -r -x archive*"
    ]

    for cmd in archive_commands:
        logging.info("With this command: '%s'" % cmd)
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=container_path,
            shell=True
        )
        out, err = p.communicate()
        if out or err:
            logging.info("archiver said out(%s) err(%s)" % (out, err))

def bptimes(conf, cwd, result_path, output_path):
    """
    Execute the bp-times command for the given result-file and output-file.
    """

    result_fn = os.path.basename(result_path)
    result_id = os.path.splitext(result_fn)[0]

    logging.info("Getting times for '%s'" % result_id)

    cmd = [                                     # Construct command
        "bp-times",
        result_path,
    ]
    cmd_str = " ".join(cmd)
    logging.info("Running: `%s`" % cmd_str)

    with(open(output_path, 'w')) as output_fd:  # Open the output file..
        p = subprocess.Popen(                   # ..pipe results into it.
            cmd,
            stdout=output_fd,
            stderr=subprocess.PIPE,
            cwd=cwd
        )
        out, err = p.communicate()
        if err:
            logging.error("The command threw up the following error: [%s]" % err)

    return (out, err)

def move_container(conf, container_path, dest):
    """
    Move the container around...
    Returns the abspath where it is moved to.
    """

    (container_id, suitename, suite_path, result_path) = get_container_info(
        conf, container_path
    )
    
    logging.info("Move(%s) -> %s" % (container_id, dest))   # Check destination
    if dest not in conf.paths:
        raise Exception("Invalid destination %s" % dest)

    dest_path = os.sep.join([conf.paths[dest], container_id])
    if os.path.exists(dest_path):                           # Check for conflict
        logging.info("Conflict, changing container_id / dest_path.")
        postfix = id_generator()
        dest_path = ".".join([
            dest_path,
            postfix
        ])
    
    logging.info("mv %s -> %s" % (container_path, dest_path))
    os.rename(container_path, dest_path)                    # Move it

    return dest_path

def make_container(conf, container_id, suitename):
    """
    Create a container for the suite in the 'running' dir.
    Returns None on failure and the abspath to the container on success.
    """
    
    container_path = os.sep.join([conf.run_dir, container_id])
    if os.path.exists(container_path):
        logging.info("Container(%s) exists, skipping." % container_id)
        return None

    logging.info("Creating container(%s)" % container_path)
    os.mkdir(container_path)

    suitename_path = os.sep.join([container_path, "%s.suitename" % suitename])
    touch(suitename_path)

    return container_path

def get_container_info(conf, container_path):
    """Returns info about the container."""

    container_id = os.path.basename(container_path)             # Get the container_id

    suitename = None                                            # Get the suitename
    for i, filename in enumerate(glob.glob(os.sep.join([container_path, "*.suitename"]))):
        suitename = os.path.splitext(os.path.basename(filename))[0]
        if i > 0:
            raise Exception("Too many suite-names!")

    if not suitename or suitename not in conf.suites:
        raise Exception("Invalid suite(%s)" % suitename)
    
    suite_path = conf.suites[suitename]                         # Get the suite_path
    result_path = os.sep.join([container_path, "result.json"])  # Get the result_path

    logging.info("container_id(%s), suitename(%s), container_path(%s), result_path(%s)" % (
        container_id, suitename, container_path, result_path
    ))

    return (container_id, suitename, suite_path, result_path)

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
            container_id = "%s-%s" % (suitename, postfix)
            container_path = make_container(conf, container_id, suitename)

def check_running(conf):
    """
    Check running jobs.

    When finished move to "postprocessing"
    """

    for container_path in listdir(conf.run_dir):

        (container_id, suitename, suite_path, result_path) = get_container_info(
            conf, container_path
        )

        out, err = bprun(conf, container_path, suite_path, result_path) # RUN!

        if "Benchmark all finished" in out:             # Check the status
            logging.info("Run(%s) has finished." % container_id)
   
            move_container(conf, container_path, "postprocess")

def check_postprocessing(conf):
    """
    Check if there is anything waiting to get processed, then:

        * run bp-times
        * run bp-grapher (when applicable)
        * create tar-archive
        * move into "done"

    """
    for container_path in listdir(conf.postprocess_dir):

        (container_id, suitename, suite_path, result_path) = get_container_info(
            conf, container_path
        )
        times_path = os.sep.join([container_path, "times.txt"]) # Dump times
        bptimes(conf, container_path, result_path, times_path)

        result = json.load(open(result_path))                   # Dump graphs
        if "use_grapher" in result["meta"]:
            use_grapher = result["meta"]["use_grapher"]
            if use_grapher:
                graph_path = os.sep.join([container_path, "graphs"])
                logging.info("use_grapher(%s), graph_path(%s)" % (
                    use_grapher, graph_path
                ))

                try:
                    os.mkdir(graph_path)
                except OSError as e:
                    logging.info("Graph-dir already exist?")

                out, err = bpgrapher(                           # Graphing...
                    conf, graph_path, "cpu", result_path, graph_path
                ) 
                logging.info("bpgrapher said: out(%s), err(%s)" % (out, err))

        
        archive_container(conf, container_path)     # Create container-archive
        move_container(conf, container_path, "done")# Move it all into done!

TASKS = {
    "watch": check_watching,
    "run": check_running,
    "postprocess": check_postprocessing
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
    logging.info("========= +++ '%s' +++ =========" % args.task)
    TASKS[args.task](conf)
    logging.info("========= ... '%s' ... =========" % args.task)

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
        help="Path to a REPOS, the revision is included in the result."
    )
    parser.add_argument(
        'task',
        type=str,
        help="What do you want to do.",
        choices=[task for task in TASKS]
    )
    args = parser.parse_args()
    main(args)
