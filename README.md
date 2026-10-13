# VisionAccess Add-on Sharer

* Author: Mukesh Jain, VisionAccess
* Website: [www.visionaccess.org](https://www.visionaccess.org)
* Contact: info@visionaccess.org, phone 7021030307
* Download: [latest version on GitHub](https://github.com/visionaccess/visionAccessAddonSharer/releases/latest)
* Works with: NVDA 2024.1 to 2026.2

## Download and install

1. Download the latest `.nvda-addon` file from the [Releases page](https://github.com/visionaccess/visionAccessAddonSharer/releases/latest).
2. Open the downloaded file and press Enter. NVDA asks if you want to install the add-on. Choose Yes.
3. Restart NVDA when it asks.

## What it does

This add-on turns the add-ons you have already installed in NVDA back into ready-to-install `.nvda-addon` files.

Use it to:

* keep a backup of all your add-ons before reinstalling Windows or NVDA,
* move your add-ons to a new computer,
* share an add-on with a friend or a student who cannot find it online.

## How to open it

* From the NVDA menu: Tools, then **VisionAccess Add-on Sharer**.
* Or press **NVDA+Shift+Alt+A**. You can change this key in NVDA menu, Preferences, Input Gestures, category "VisionAccess Add-on Sharer".

## How to use it

1. The focus starts on the list of installed add-ons. Move with the arrow keys and press **Space** to check each add-on you want to share. Disabled add-ons are listed too.
2. Choose where the files are saved. By default they go to the folder **Documents\NVDA Add-on Packages**. Use the **Browse** button to choose another folder. Your choice is remembered.
3. Press **Create packages**. A progress bar shows how far the work has gone.
4. When it finishes, you can copy the new files to the clipboard and paste them straight into an e-mail, WhatsApp Desktop, Telegram or a USB drive. If "Open the folder when finished" is checked, the folder opens too.

Each file is named after the add-on and its version, for example `clock-24.1.nvda-addon`. If a file with the same name is already in the folder, it is replaced with the new one.

### Keys in the window

* Alt+I: go to the add-on list
* Alt+A: check all add-ons
* Alt+U: uncheck all add-ons
* Alt+F: go to the output folder field
* Alt+B: browse for another folder
* Alt+O: open the folder when finished (on or off)
* Alt+C: create the packages
* Alt+L or Escape: close the window

## Please note

* The package contains the add-on folder exactly as it is on your computer. Temporary Python cache files (`__pycache__`) are left out. Some add-ons keep personal settings inside their own folder, and these settings go into the package too. Keep this in mind before you share a file publicly.
* Please respect each add-on author's licence. Most NVDA add-ons are free and open source, but for paid or licensed add-ons, ask the author before you share them.
* For safety, the add-on does not work on secure screens such as the Windows sign-in screen.

## Credits

The idea comes from the "Add-on Packer" add-on by Héctor J. Benítez Corredera. VisionAccess Add-on Sharer is a new add-on written for current NVDA versions.

## Changes

### Version 1.0.2

* The add-on description now lists all keyboard commands.
* Added the download link for the latest version.

### Version 1.0.1

* Fixed: the window did not open from the Tools menu or with NVDA+Shift+Alt+A.

### Version 1.0.0

* First release.
