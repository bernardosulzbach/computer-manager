#!/usr/bin/env bash

# Add the snap repository.
sudo zypper addrepo --refresh https://download.opensuse.org/repositories/system:/snappy/openSUSE_Tumbleweed snappy
# Import the GPG key.
sudo zypper --gpg-auto-import-keys refresh
# Finally, upgrade the package cache to include the new snappy repository.
sudo zypper dup --from snappy
# Install snap.
sudo zypper install snapd
