import sys
import os
import errno

def get_opt_arg(opt_index):
    arg_index = opt_index + 1
    if arg_index >= len(sys.argv):
        sys.exit("Error: option '%s' requires an argument" % sys.argv[opt_index])
    return arg_index, sys.argv[arg_index]

def check_arg_count(usage, args, **kwargs):
    actual = len(args)
    if "exact" in kwargs:
        expected = kwargs["exact"]
        if actual == 0 and expected > 0:
            usage()
            sys.exit(1)
        if actual < expected:
            sys.exit("Error: not enough command line arguments, expected %s but got %s" % (expected, actual))
        if actual > expected:
            sys.exit("Error: too many command line arguments, expected %s but got %s" % (expected, actual))
    if "min" in kwargs:
        min = kwargs["min"]
        if actual == 0 and min > 0:
            usage()
            sys.exit(1)
        if actual < min:
            sys.exit("Error: not enough command line arguments, need at least %s but got %s" % (min, actual))
    if "max" in kwargs:
        max = kwargs["max"]
        if actual > max:
            sys.exit("Error: too many command line arguments, max is %s but got %s" % (max, actual))

def stat_nothrow(path):
    try:
        return os.stat(path)
    except:
        return None

def clean_pathname(path):
    if path.startswith("./"):
        return path[2:]
    return path

def correct_path(path, base):
    if os.path.isabs(path):
        return path
    return os.path.join(base, path)

def is_bind_mount(path):
    # http://blog.schmorp.de/2016-03-03-detecting-a-mount-point.html
    # This is a hack to determine if a path is a bind mount. It attempts
    # to do an invalid rename which will fail with a different error code
    # depending on if it is a bind mount or not
    try:
        old = os.path.join(path, "..") + "/."
        new =  path + "/."
        os.rename(old, new)
        sys.exit("Error: is_bind_mount relies on an invalid rename but it worked!??! old '%s' new '%s'" % (old, new))
    except OSError as err:
        if err.errno == errno.EXDEV:
            return True
        return False

def yes_or_no(question):
    while True:
        sys.stdout.write(question + " [y/n] ")
        response = input()
        if response == "y":
            return True
        elif response == "n":
            return False
