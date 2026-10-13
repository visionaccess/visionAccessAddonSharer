# -*- coding: UTF-8 -*-
# VisionAccess Add-on Sharer - packaging helpers.
# Copyright (C) 2026 Mukesh Jain, VisionAccess (www.visionaccess.org)
# Released under GNU General Public License version 2.
# This module has no NVDA dependencies so it can be tested on its own.

import os
import re
import zipfile

ADDON_EXTENSION = ".nvda-addon"

# Folders and files that are created by Python at run time and must not be shipped.
_SKIP_DIRS = {"__pycache__"}
_SKIP_EXTENSIONS = {".pyc", ".pyo"}


def safeFileName(text):
	"""Return text with characters that Windows does not allow in file names removed."""
	text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(text)).strip(" .")
	return text or "addon"


def packageFileName(name, version):
	"""Build the output file name, for example clock-2.1.nvda-addon"""
	base = safeFileName(name)
	if version:
		base = "%s-%s" % (base, safeFileName(version))
	return base + ADDON_EXTENSION


def collectFiles(sourceDir):
	"""Yield (fullPath, pathInsideZip) for every file to include from sourceDir."""
	for root, dirs, files in os.walk(sourceDir):
		dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS)
		for fileName in sorted(files):
			if os.path.splitext(fileName)[1].lower() in _SKIP_EXTENSIONS:
				continue
			fullPath = os.path.join(root, fileName)
			arcName = os.path.relpath(fullPath, sourceDir).replace(os.sep, "/")
			yield fullPath, arcName


def packAddon(sourceDir, destFile):
	"""Zip the installed add-on folder sourceDir into destFile (.nvda-addon).
	The file is first written under a temporary name and then moved into place,
	so a failure never leaves a half-written package behind.
	Returns the number of files packed."""
	if not os.path.isfile(os.path.join(sourceDir, "manifest.ini")):
		raise ValueError("manifest.ini not found in %s" % sourceDir)
	tempFile = destFile + ".part"
	count = 0
	try:
		with zipfile.ZipFile(tempFile, "w", zipfile.ZIP_DEFLATED) as z:
			for fullPath, arcName in collectFiles(sourceDir):
				z.write(fullPath, arcName)
				count += 1
		os.replace(tempFile, destFile)
	finally:
		if os.path.exists(tempFile):
			os.remove(tempFile)
	return count
