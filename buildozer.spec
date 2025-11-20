[app]
title = Finansor
package.name = finansor
package.domain = org.finans
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.2.0,kivymd,pillow,sqlite3,urllib3
icon.filename = %(source.dir)s/icon.png
orientation = portrait
android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.skip_update = False
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
