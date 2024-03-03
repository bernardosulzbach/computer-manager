# Syncthing

On the remote Arch VPS $REMOTE, run

```
pacman -S syncthing
useradd --system -s /usr/bin/nologin syncthing -U
mkdir /home/syncthing
chown syncthing:syncthing /home/syncthing
systemctl enable syncthing@syncthing.service
systemctl start syncthing@syncthing.service
```

then, on your machine, run

```
ssh -L 49152:localhost:8384 root@$REMOTE
```

to make the web GUI accessible at `localhost:49152`.
