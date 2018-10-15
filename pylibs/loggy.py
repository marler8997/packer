import os
import sys
import subprocess
import shutil

enable = False

def rmtree(path):
    if enable:
        print("rmtree '%s'" %path)
    shutil.rmtree(path)

def rmtreeIfExists(path):
    if (os.path.exists(path)):
        if enable:
            print("rmtree '%s'" %path)
        shutil.rmtree(path)

def remove(pathname):
    if enable:
        print("rm '%s'" % pathname)
    os.remove(pathname)

def rmdir(path):
    if enable:
        print("rmdir '%s'" % path)
    os.rmdir(path)

def removeIfExists(pathname):
    if (os.path.exists(pathname)):
        if enable:
            print("rm '%s'" % pathname)
        os.remove(pathname)

def symlink(src, dst):
    if enable:
        print("symlink '%s' -> '%s'" % (dst, src))
    os.symlink(src, dst)

def mkdir(path):
    if enable:
        print("mkdir '%s'" % path)
    os.mkdir(path)

def makedirs(path):
    if enable:
        print("makedirs '%s'" % path)
    os.makedirs(path)

def chdir(path):
    if enable:
        print("chdir '%s'" % path)
    os.chdir(path)

def rename(src, dst):
    if enable:
        print("rename '%s' to '%s'" % (src, dst))
    os.rename(src, dst)

def copyfileAndMode(src, dst):
    if enable:
        print("copy (with mode) '%s' to '%s'" % (src, dst))
    shutil.copyfile(src, dst)
    shutil.copymode(src, dst)

def system(cmd):
    if enable:
        print("[SHELL] ", cmd)
    exitCode = os.system(cmd)
    if exitCode != 0:
        sys.exit("last command failed, exit code %s" % exitCode)

def run(*args, **kwargs):
    stdin = kwargs.get("stdin")
    redirect = kwargs.get("stdout")
    cwd = kwargs.get("cwd")
    if enable:
        print("[SHELL] " +
              ("(cd " + cwd + "; " if cwd else "") +
              subprocess.list2cmdline(*args) +
              (" < " + stdin.name if stdin else "") +
              (" > " + redirect.name if redirect else "") +
              (")" if cwd else ""))
        sys.stdout.flush()
    return subprocess.check_call(*args, **kwargs)

def run_output(*args, **kwargs):
    if enable:
        print("[SHELL] " + subprocess.list2cmdline(*args))
        sys.stdout.flush()
    return subprocess.check_output(*args, **kwargs)

def execvp(args):
    if enable:
        print("[exec] " + subprocess.list2cmdline(args))
        sys.stdout.flush()
    os.execvp(args[0], args)
