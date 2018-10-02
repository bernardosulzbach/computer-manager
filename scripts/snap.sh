#!/usr/bin/env bash
sudo zypper addrepo --refresh http://download.opensuse.org/repositories/system:/snappy/openSUSE_Tumbleweed/ snappy
sudo zypper install snapd
sudo systemctl enable --now snapd.socket
