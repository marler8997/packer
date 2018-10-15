import sys
import os
import stat
import uuid
import json

script_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(script_dir, "pylibs"))

import util
import loggy
import jsongen

def gen_config(config_filename, args):
    with open(config_filename, "w") as config_file:
        gen = jsongen.JsonGenerator(config_file)
        gen.start()
        gen.obj()

        gen.prop_str("ociVersion", "1.0.0")
        #
        # process
        #
        gen.prop_obj("process")
        gen.prop_bool("terminal", True)
        gen.prop_obj("user")
        gen.prop_val("uid", 0)
        gen.prop_val("gid", 0)
        gen.end_obj()
        gen.prop_array("args")
        for arg in args:
            gen.str(arg)
        gen.end_array()
        gen.prop_array("env")
        gen.str("PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")
        gen.str("TERM=xterm")
        if "http_proxy" in os.environ:
            gen.str("http_proxy=%s" % os.environ["http_proxy"])
        if "https_proxy" in os.environ:
            gen.str("https_proxy=%s" % os.environ["https_proxy"])
        gen.end_array()
        gen.prop_str("cwd", "/")

        gen.prop_obj("capabilities")
        for cap_type in ("bounding", "effective", "inheritable",
                         "permitted", "ambient"):
            gen.prop_array(cap_type)
            gen.str("CAP_AUDIT_WRITE")
            gen.str("CAP_KILL")
            gen.str("CAP_NET_BIND_SERVICE")
            gen.end_array()
        gen.end_obj()

        gen.prop_array("rlimits")
        gen.obj()
        gen.prop_str("type", "RLIMIT_NOFILE")
        gen.prop_val("hard", 1024)
        gen.prop_val("soft", 1024)
        gen.end_obj()
        gen.end_array()
        gen.prop_bool("noNewPrivileges", True)

        gen.end_obj();
        #
        # root
        #
        gen.prop_obj("root")
        gen.prop_str("path", "../rootfs")
        gen.prop_bool("readonly", False)
        gen.end_obj()
        #
        # hostname
        #
        #gen.prop_str("hostname", "runc")
        #
        # mounts
        #
        gen.prop_array("mounts")
        for dest,type,source,options in (
                ("/proc", "proc", "proc", None),
                ("/dev", "tmpfs", "tmpfs", ["nosuid","strictatime","mode=755","size=65536k"]),
                ("/dev/pts", "devpts", "devpts", ["nosuid","noexec","newinstance","ptmxmode=0666","mode=0620"]),
                ("/dev/shm", "tmpfs", "shm", ["nosuid","noexec","nodev","mode=1777","size=65536k"]),
                ("/dev/mqueue", "mqueue", "mqueue", ["nosuid","noexec","nodev"]),
                ("/sys", "none", "/sys", ["rbind","nosuid","noexec","nodev","ro"]),
                ):
            gen.obj()
            gen.prop_str("destination", dest)
            gen.prop_str("type", type)
            gen.prop_str("source", source)
            if options != None:
                gen.prop_array("options")
                for opt in options:
                    gen.str(opt)
                gen.end_array()

            gen.end_obj()
        gen.end_array()
        #
        # linux
        #
        gen.prop_obj("linux")

        gen.prop_array("namespaces")
        for ns in (
                "pid",
                "ipc",
                "uts",
                "mount",
                "user"):
            gen.obj()
            gen.prop_str("type", ns)
            gen.end_obj()
        gen.end_array()

        for mapping in ("uidMappings", "gidMappings"):
            gen.prop_array(mapping)
            gen.obj()
            gen.prop_val("containerID", 0)
            gen.prop_val("hostID", 1000)
            gen.prop_val("size", 1)
            gen.end_obj()
            # allow apt to run
            #gen.obj()
            #gen.prop_val("containerID", 65534)
            #gen.prop_val("hostID", 1000)
            #gen.prop_val("size", 1)
            #gen.end_obj()
            gen.end_array()

        gen.prop_array("maskedPaths")
        gen.str("/proc/kcore")
        gen.str("/proc/latency_stats")
        gen.str("/proc/timer_list")
        gen.str("/proc/timer_stats")
        gen.str("/proc/sched_debug")
        gen.str("/proc/scsi")
        gen.str("/sys/firmware")
        gen.end_array()
        gen.prop_array("readonlyPaths")
        gen.str("/proc/asound")
        gen.str("/proc/bus")
        gen.str("/proc/fs")
        gen.str("/proc/irq")
        gen.str("/proc/sys")
        gen.str("/proc/sysrq-trigger")
        gen.end_array()

        gen.end_obj()


        gen.end_obj()
        gen.finish()

def mount_base_rootfs(base_arg, base_arg_stat, mount_point):
    if stat.S_ISDIR(base_arg_stat.st_mode):
        loggy.run(["sudo", "mount", "--bind", "-o", "ro", base_arg, mount_point])
        return

    if not stat.S_ISREG(base_arg_stat.st_mode):
        sys.exit("Error: base '%s' is not a file or a directory (mode=0x%x)" % (base_arg, base_arg_stat.st_mode))

    if base_arg.endswith(".tar"):
        loggy.run(["archivemount",
                   "-o", "readonly",
                   base_arg, mount_point])
    elif base_arg.endswith(".sq"):
        # use sudo...a hack
        loggy.run(["sudo", "mount",
                   "-t","squashfs",
                   base_arg, mount_point])
    else:
        sys.exit("Error: base file has unknown extension '%s', expected .tar, .sq or .json" % base_arg)

def mount_base_from_json(original_json_filename, copied_json_filename, mount_point):
    with open(copied_json_filename, "r") as file:
        config = json.load(file)
    if not "base-image" in config:
        sys.exit("Error: '%s' does not contain a \"base-image\" property" % original_json_filename)
    base_image = util.correct_path(config["base-image"], os.path.dirname(original_json_filename))
    base_image_stat = util.stat_nothrow(base_image)
    if base_image_stat == None:
        sys.exit("Error: base-image '%s' does not exist" % base_image)
    mount_base_rootfs(base_image, base_image_stat, mount_point)

def enforce_valid_overlay_name(name, can_be_base):
    if name == ".packer_repo" or name == "packs":
        sys.exit("Error: '%s' is not a valid overlay name (it is reserved)" % name)
    if (not can_be_base) and name == "base":
        sys.exit("Error: '%s' is not a valid overlay name (it is reserved)" % name)
    if os.sep in name:
        sys.exit("Error: '%s' is not a valid overlay name (contains '%s')" % (name, os.sep))

def enforce_is_packer_repo(packer_dir, packer_dir_stat):
    # TODO: maybe do more verification?
    if packer_dir_stat == None:
        sys.exit("Error: not a packer repo, missing '%s'" % packer_dir)
    if not stat.S_ISDIR(packer_dir_stat.st_mode):
        sys.exit("Error: not a packer repo, '%s' is not a directory" % packer_dir)

def increment_name(name):
    name_len = len(name)
    if name[name_len - 1] == 'z':
        sys.exit("Error: increment_name not fully implemented")
    return name[:name_len - 1] + chr(ord(name[name_len - 1]) + 1)

def new_ordered_dir(parent_dir):
    # TODO: get a better overlay_basename naming scheme if one is not specified
    # TODO: should there be a max number of attempts?
    next_name = "a"
    while True:
        dir = os.path.join(parent_dir, next_name)
        # TODO: faster to check os.path.exists first?
        try:
            loggy.mkdir(dir)
            return dir
        except FileExistsError:
            pass
        next_name = increment_name(next_name)

class LowerDirBuilder:
    def __init__(self, repo_dir):
        self.repo_dir = repo_dir
        self.added = []
        self.lower_dirs = ""
    def add_parents(self, parents):
        for parent in parents.split(","):
            self._add_parent(parent)
    def _add_parent(self, parent):
        if parent in self.added:
            return
        # add immediately so recursive calls don't add
        self.added.append(parent)
        if parent == "base":
            dir = os.path.join(self.repo_dir, parent, "rootfs")
        else:
            parents_file = os.path.join(self.repo_dir, parent, "parents")
            if not os.path.exists(parents_file):
                sys.exit("Error: invalid parent '%s' (file '%s' does not exist)" % (parent, parents_file))
            with open(parents_file, "r") as file:
                grandparents = file.read()
            self.add_parents(grandparents)
            dir = os.path.join(self.repo_dir, parent, "overlay")

        if not os.path.exists(dir):
            sys.exit("Error: invalid parent '%s' (dir '%s' does not exist)" % dir)
        if len(self.lower_dirs) > 0:
            self.lower_dirs += ":"
        self.lower_dirs += dir

def _finish_overlay(repo_dir, parents, overlay_dir):
    builder = LowerDirBuilder(repo_dir)
    builder.add_parents(parents)
    if len(builder.lower_dirs) == 0:
        sys.exit("Error: no parents were given")

    # save real parents
    parents_file = os.path.join(overlay_dir, "parents")
    with open(parents_file, "w") as file:
        file.write(",".join(builder.added))

    mount_overlay(builder.lower_dirs, overlay_dir)
def new_overlay(repo_dir, parents, name):
    enforce_valid_overlay_name(name, False)
    overlay_dir = os.path.join(repo_dir, name)
    if os.path.exists(overlay_dir):
        sys.exit("Error: overlay '%s' already exists" % name)
    loggy.mkdir(overlay_dir)
    _finish_overlay(repo_dir, parents, overlay_dir)
def new_overlay_generate_name(repo_dir, parents):
    overlay_dir = new_ordered_dir(repo_dir)
    _finish_overlay(repo_dir, parents, overlay_dir)
    return overlay_dir

def mount_overlay(lower_dirs, overlay_dir):
    rootfs_overlay = os.path.join(overlay_dir, "rootfs")
    overlay_upper = os.path.join(overlay_dir, "overlay")
    overlay_work  = os.path.join(overlay_dir, ".overlay_work")
    loggy.mkdir(rootfs_overlay)
    loggy.mkdir(overlay_upper)
    loggy.mkdir(overlay_work)
    # use sudo...a hack
    loggy.run(["sudo", "mount", "-t", "overlay", "overlay", rootfs_overlay, "-o",
               "rw,lowerdir=%s,upperdir=%s,workdir=%s" % (lower_dirs, overlay_upper, overlay_work)])
    return rootfs_overlay

def run_bundle(bundle_dir):
    container_id = str(uuid.uuid4())
    loggy.execvp(["runc",
                  # TODO: not sure what --rootless does
                  "--rootless", "true",
                  #"--log", os.path.join(bundle_dir, container_id + ".log"),
                  "--debug",
                  "run",
                  "--bundle", bundle_dir,
                  container_id])

def run(base_or_overlay_dir, args):
    bundle_dir = new_ordered_dir(base_or_overlay_dir)
    config_filename = os.path.join(bundle_dir, "config.json")
    gen_config(config_filename, args)
    run_bundle(bundle_dir)

# returns: the nmber of entries it failed to remove
# assumption: dir is already verified to be a directory
# root_dev is the device number of the directory in the filesystem you
# are wanting to clean from
# clean_dir uses this to know when a subdirectory is just a mount point to
# another filesystem.  it will then proceed to unmount instead of removing
# files inside the mount point
def clean_dir(root_dev, dir, dir_stat):
    #print("[DEBUG] clean_dir '%s'" % dir)
    error_count = 0
    while dir_stat.st_dev != root_dev or util.is_bind_mount(dir):
        # TODO: maybe this loop should have a max number of attempts?
        loggy.run(["sudo", "umount", dir])
        dir_stat = os.stat(dir) # TODO: maybe we handle errors when this fails?

    try:
        entries = os.listdir(dir)
    except PermissionError as err:
        print("WARNING: access denied to list files in '%s'" % dir)
        # don't increase fail count yet, rmdir still might work
        entries = iter([])

    for entry_basename in entries:
        entry = os.path.join(dir, entry_basename)
        entry_stat = os.lstat(entry)
        if entry_stat == None:
            print("Error: stat failed for '%s'" % entry)
            error_count += 1
        elif stat.S_ISDIR(entry_stat.st_mode):
            error_count += clean_dir(root_dev, entry, entry_stat)
        else:
            if entry_stat.st_dev != root_dev:
                sys.exit("Error: file '%s' has different st_dev than its parent directory...didn't know this could happen" % entry)
            #if not stat.S_ISREG(rootfs_stat.st_mode):
            loggy.remove(entry)
    try:
        loggy.rmdir(dir)
    except OSError as err:
        try:
            loggy.run(["sudo", "rmdir", dir])
        except:
            err = sys.exc_info()[0]
            print("Error: failed to remove directory '%s': %s" % (dir, err))
            error_count += 1
    return error_count

# returns: the number of entries it failed to remove
def clean_overlay(repo_dev, overlay_dir, overlay_stat):
    # TODO: maybe we should verify that this is a overlay?

    # HACK: remove the special 'work' directory that is cannot be deleted by non-root users
    #pesky_work_dir = os.path.join(overlay_dir, ".overlay_work", "work")
    #if os.path.exists(pesky_work_dir):
    #    loggy.run(["sudo", "rmdir", pesky_work_dir])
    return clean_dir(repo_dev, overlay_dir, overlay_stat)

def clean_repo(repo_dir, repo_stat, is_purge):
    error_count = 0
    for entry_basename in os.listdir(repo_dir):
        if entry_basename == ".packer_repo":
            continue # remove last, and only if there are no errors
        if not is_purge:
            if entry_basename == "base" or entry_basename == "patched":
                continue
        entry = os.path.join(repo_dir, entry_basename)
        entry_stat = util.stat_nothrow(entry)
        if entry_stat == None:
            sys.exit("Error: stat on '%s' failed" % entry)
        if stat.S_ISDIR(entry_stat.st_mode):
            # TODO: maybe we should verify it is an overlay?
            error_count += clean_overlay(repo_stat.st_dev, entry, entry_stat)
        else:
            print("WARNING: extra file '%s', it is not a known file or a overlay")
    if is_purge and error_count == 0:
        packer_dir = os.path.join(repo_dir, ".packer_repo")
        return clean_dir(repo_stat.st_dev, packer_dir, os.stat(packer_dir))
    return error_count

class PackerImageJson:
    def __init__(self, filename):
        self.filename = filename;
        with open(filename, "r") as file:
            json_obj = json.load(file)
        if not "base-image" in json_obj:
            sys.exit("Error: %s is missing the 'base-image' property" % filename)
        self.base_image = json_obj["base-image"]
        if "package-paths" in json_obj:
            # TODO: check that paths are valid? need to be absolute right?
            self.package_paths = json_obj["package-paths"]
