#!/usr/bin/python3
import hashlib
import time
import random

import executor
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta

import sys
import os
import socket
import json
import threading
import subprocess

from ykman import list_all_devices, scan_devices

owner = os.environ.get("YUBIKEY_GDM_UNLOCKER_OWNER", os.getuid())

USE_BROKER = 'YUBIKEY_GDM_UNLOCKER_MQTT' in os.environ
if USE_BROKER:
    broker = os.environ.get("YUBIKEY_GDM_UNLOCKER_MQTT", "127.0.0.1")
    broker_user = os.environ.get("YUBIKEY_GDM_UNLOCKER_MQTT_USER", "")
    broker_pass = os.environ.get("YUBIKEY_GDM_UNLOCKER_MQTT_PASS", "")
    group = os.environ.get("YUBIKEY_GDM_UNLOCKER_GROUP", "")
    device = os.environ.get("YUBIKEY_GDM_UNLOCKER_DEVICE", "") or socket.gethostname()
    group_topic = os.path.join("/yubikey_gdm_unlocker", group)
    device_topic = os.path.join(group_topic, device)
    owner_topic = os.path.join(device_topic, owner)
    mqtt_interval = int(os.environ.get("YUBIKEY_GDM_UNLOCKER_CHECKIN_INTERVAL", "12"))

ACTIVITY_DIR = os.environ.get("YUBIKEY_GDM_UNLOCKER_ACTIVITY_DIR", "/tmp/activity")
yubikey_interval = int(os.environ.get("YUBIKEY_GDM_UNLOCKER_YUBIKEY_INTERVAL", "1"))
unlock_yubikeys = [
    k.lstrip("0").strip() for k in os.environ.get("YUBIKEY_GDM_UNLOCKER_YUBIKEYS", "").split(",") if k
]


def debug(*args):
    print(datetime.now().strftime("%c"), *args)


def get_user_loginctl_prop(user, prop):
    return subprocess.run("loginctl show-user %s -p %s --value" % (user, prop), capture_output=True, check=False,
                          shell=True).stdout.decode("utf-8")


def user_activity(user):
    return {
        "user.idle": get_user_loginctl_prop(user, "IdleHint"),
        "user.linger": get_user_loginctl_prop(user, "Linger"),
        "user.state": get_user_loginctl_prop(user, "State"),
        "system.sessions": len(get_user_loginctl_prop(user, "Sessions").split(",")),
        "system.caffeinate": caffeinate_running() and 1 or 0,
        "system.yubikeys": len(GLOBAL_PLUGGED_DEVICES),
        "_keys": GLOBAL_PLUGGED_DEVICES,
        "_pid": os.getpid(),
        "_at": time.time(),
    }


def publish_user_activity(client, user, activity):
    for key, value in activity.items():
        if key.startswith("_"):
            continue
        topic = os.path.join(device_topic, user, key)
        client.publish(topic, value)

    with open(os.path.join(ACTIVITY_DIR, "%s.json" % user), "w+") as fh:
        fh.write(json.dumps(activity))


def plugged_yubikeys():
    return [info.serial for d, info in list_all_devices()]


def usb_device_hash():
    # YKMan method
    return hashlib.md5(json.dumps(scan_devices()).encode()).hexdigest()


def check_pid(pid):
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def caffeinate_running():
    try:
        return subprocess.check_output(["pgrep", "caffeinate"]).decode("utf-8").strip().split()
    except Exception as e:
        return []


def publish_forever():
    # Send messages in a loop
    client = mqtt.Client("ha-client")
    client.username_pw_set(broker_user, broker_pass)
    client.connect(broker)
    client.loop_start()
    last_printed = datetime.now()

    def needs_print():
        return (datetime.now() - last_printed) > timedelta(minutes=2)

    while True:
        activity = user_activity(owner)
        if needs_print():
            last_printed = datetime.now()
            debug(
                {
                    k: v
                    for k, v in activity.items()
                    if k.startswith("system")
                }
            )
        publish_user_activity(client, owner, activity)

        time.sleep(mqtt_interval)


GLOBAL_LAST_DEVICE_HASH = None
GLOBAL_PLUGGED_DEVICES = []


def unlock_forever():
    global GLOBAL_LAST_DEVICE_HASH
    global GLOBAL_PLUGGED_DEVICES
    if not unlock_yubikeys:
        debug("no key to unlock")
        return
    time.sleep(0.5)

    last_checked = datetime.now()

    def needs_check():
        return (datetime.now() - last_checked) > timedelta(minutes=3)

    while True:
        time.sleep(yubikey_interval)
        current_hash = usb_device_hash()
        if not needs_check() and GLOBAL_LAST_DEVICE_HASH == current_hash:
            continue
        else:
            GLOBAL_LAST_DEVICE_HASH = current_hash
            last_checked = datetime.now()

        running = caffeinate_running()
        try:
            GLOBAL_PLUGGED_DEVICES = plugged_yubikeys()
            key = str(GLOBAL_PLUGGED_DEVICES[0])
            valid_key = key in unlock_yubikeys
        except:
            GLOBAL_PLUGGED_DEVICES = []
            valid_key = None

        print("plugged yubikeys", current_hash, GLOBAL_PLUGGED_DEVICES)

        if valid_key:
            if not running:
                fn = os.path.join(os.path.dirname(os.path.realpath(__file__)), "unlock.sh")
                debug("keys: unlocking with %s..."%fn)
                subprocess.Popen(fn, shell=True)
        elif running:  # invalid and running
            debug("keys: not valid, stopping", running)
            for pid in running:
                subprocess.run(
                    "kill -9 %s" % pid,
                    shell=True,
                    check=False,
                    capture_output=False
                )


if __name__ == "__main__":
    user = owner
    fn = os.path.join(ACTIVITY_DIR, "%s.json" % user)
    if not os.path.exists(ACTIVITY_DIR):
        os.mkdir(ACTIVITY_DIR)

    if os.path.exists(fn):
        old_data = json.loads(open(fn, "r").read())
        if check_pid(old_data["_pid"]):
            if "-r" in sys.argv:
                debug("Already running as pid %s, restarting..." % old_data["_pid"])
                executor.execute("kill -9 %s" % old_data["_pid"], shell=True, check=False)
                time.sleep(1)
            else:
                debug("Already running as pid %s" % old_data["_pid"])
                sys.exit(1)

    if USE_BROKER:
        publisher = threading.Thread(target=publish_forever, daemon=True)
        publisher.start()
    unlocker = threading.Thread(target=unlock_forever, daemon=True)
    unlocker.start()
    unlocker.join()
