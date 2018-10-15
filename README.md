
# Packer

Packer provides a way to manage/build container images. It breaks software down into isolated "packs" that can be applied individually. These packs can then be applied when launching a container to create a combination of all the software that is need for a particular contiainer instance.

# Install

1. Clone this repo
2. Install "runc" (see instructions below)
3. Create symbolic link to `<repo>/packer` somewhere in `PATH`

```
ln -s <somewhere_in_PATH>/packer <this_repo>/packer
```

For convenience, the provided `install` will assist in selecting a path to install `packer` to:
```
./install
```

# Usage

Packer works inside "repositores".  A repository contains a "base image" along with a set of "overlay images" that provide various "views" of the base image.  The base image can be a directory, a squashfs file, a tar file, or made from a docker image (see "Starting from a docker image"). The following will initialize a packer repository with the given base image:
```bash
packer init <base-image>
```

At this point we can start a container with our base image:

```bash
packer run base <program> <args>...
```

Inside this container no changes can be made because the base image is alway mounted as readonly. Once packer has created a base image, the user is able to create "overlay images". An overlay image is a filesystem that gets overlayed on top of another image. Packer creates an initial overlay image called "patched" that "patches in" some host-specific settings like DNS.  The "patched" image is also the default parent of any new overlay images created by the user. To start a container with the "patched" image you can run:

```bash
packer run patched <program> <args>...
```

Unlike the base image, changes can be made to the files in a "patched" image container.  However, any changes you make to this image will automatically be reflected in any overlay images based of this one.  Since "patched" is the default "parent" image, this means that it will affect all other overlay images by default.

To create your own overlay image, you can run the following:
```bash
packer new [image-name]
```

This will create a new directory, either with "image-name" or a generated name.  Like the other images, you can launch a container inside the new image with the `run` command:
```
packer run <image-name> <program> <args>...
```

Like the "patched" image, this "overlay image" is writeable. All changes are written to `<image-name>/overlay` and none of them will appear in the "base" or "patched" images.


# Starting from a docker image

If you'd like to use a docker image as a "base image" for packer, you can do so by downloading and extracting it.  To download a docker image, run:
```bash
docker pull <image>
```
Example:
```
docker pull alpine:3.7
```

Then run the following to extract it:
```bash
docker save <image> | packer flatten-docker-image <output_file>.tar
```

Or you could save it to a file then extract it:

```bash
docker save <image> -o <dockerimage_tar>
packer flatten-docker-image <output_file>.tar < <dockerimage_tar>
```

## Install Runc

`packer` depends on `runc`, a command line program to launch containers: https://github.com/opencontainers/runc
You can either use your distro's package manager to install it or build it yourself using the instructions below.

### Ubuntu Install

```
sudo apt install runc
```

### Build runc

If you choose to build `runc`, you'll need the `go` compiler. It can be installed with these BASH commands, or you can use the provided `install_go` script:

> NOTE: go's install location is also where it will store globally shared libraries/programs, such as `runc`.  This guide assume you install it to your home directory `~`.

```bash
# Download binaries
cd ~
wget https://dl.google.com/go/go1.11.linux-amd64.tar.gz
tar -xzv < go1.11.linux-amd64.tar.gz
rm go1.11.linux-amd64.tar.gz

# Install to PATH
ln -s ~/go/bin/go <some_directory_in_PATH>
```

OR

```bash
./install_go <install_location> <some_directory_in_PATH>
```

Once you have `go`, the following will build `runc`

```bash
cd ~/go/src
mkdir -p github.com/opencontainers
cd github.com/opencontainers
git clone https://github.com/opencontainers/runc
cd runc

# make without libseccomp
make BUILDTAGS=""
# make with libseccomp
make

# copy the runc executable to /sbin
sudo make install
```

## jsonschema

This is a python library that is included in this repository.  It was downloaded and installed via

```bash
wget -qO- https://files.pythonhosted.org/packages/58/b9/171dbb07e18c6346090a37f03c7e74410a1a56123f847efed59af260a298/jsonschema-2.6.0.tar.gz | tar -xzv

# clean up unnecessary files
find jsonschema-2.6.0 -type f ! -name COPYING ! -wholename "*/jsonschema/*.py" ! -wholename "*/jsonschema/*.json" -exec rm {} +
rm -r jsonschema-2.6.0/jsonschema/tests
```

# Links

* https://github.com/opencontainers/runc
* https://github.com/opencontainers/runtime-spec

# TODO

* maybe don't run as "fake root" in the container by default?
* don't build images in their final directory...build them in a temp directory instead so that if they fail then packer won't think they're valid images.  probably build them in the ".packer" repo first?
* Maybe instead of typing `packer`, `pkr` would be better?  Also maybe the folder should be `.pkr` instead of `.packer`?
