# Yubikey GDM Unlocker

Unlocks your desktop based on the presence of your yubikey device.

*Please audit this code and methodology carefully* - Unlocking your device without a password is a security hole.
Running this software might be "a bad idea". Developing and releasing this software was **definitely** a "bad idea". I
don't recommend using, and I won't help you or cry for you if you are unhappy with the consequences of running this
code.

There is also some rough functionality for posting the yubikey status to MQTT; I use this for my homeassistant
automations, it is completely optional.

## Is it stable? Is it safe?

**NO**, if you are asking these questions, you shouldn't use it!

+ Stability: It's been installed on my primary desktop for a year. It runs most of the time without crashing.
+ Safety: Sometimes, Caffeine gets stuck and my monitor stays awake even after the yubikey is removed. My only solution
  is to reboot the machine.

## TO INSTALL ANYWAY

+ Requires `ykman` binary to detect yubikey presence, and uses `loginctl` and `caffienate` to wake the machine.

+ Populate .localenv with values. If you use `direnv` in your shell, some values will get populated for you, but at the
  very least, it must have the line `YUBIKEY_GDM_UNLOCKER_YUBIKEYS=xxxx,yyyy`, where xxxx and yyyy are replaced by IDs
  of your yubikey devices that you want to recognize for the unlock.

+ Give it a try for a few days - Run `service.sh` in a terminal and forget about it, you'll be able to try unlocking
  your machine with your yubikey but nothing wil persist after reboot.

+ If you want to install as a systemd service, an example is provided.

## CONTRIBUTING

Yes please! I invite all feedback and development support. I think this "security hole" is useful to me and just cool
enough to want to continue - and my own security paradigm isn't terribly compromised by somebody being able to unlock my
desktop session. If you find it useful or interesting, please contribute!