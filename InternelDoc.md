
Current implementation details
================================================================================

Each packer repository has a ".packer_repo" direcoty.  Packer uses the existence
of this directory to know it is the root of a packer repository.

A `packer init` will create ".packer_repo", it will mount a "base image" into
the `base` directory, then it will create an "overlay image" called `patched`
that patches the base image with host-specific settings.  For now the only
host-specific settings is the `/etc/resolv.conf` file.
