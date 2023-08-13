# Fixing the F keys on Varmilo keyboards

When I got myself a Varmilo Vintage Days CMYK VEM 87 ANSI in August 2023, the F
keys were not working unless combined with the Fn key.
[This Gist](https://gist.github.com/vladak/b005b0446eeb049a8b4cd546bf11dbbc)
mentions a fix from
[this ask Ubuntu answer](https://askubuntu.com/questions/7537/how-can-i-reverse-the-fn-key-on-an-apple-keyboard-so-that-f1-f2-f3-are-us/7553#7553)
that worked for me then.

Summarizing, test if

```bash
sudo bash -c "echo 2 > /sys/module/hid_apple/parameters/fnmode"
```

fixes it. If it does, then persist this change with

```bash
echo options hid_apple fnmode=2 | sudo tee -a /etc/modprobe.d/hid_apple.conf
sudo dracut --force
```
