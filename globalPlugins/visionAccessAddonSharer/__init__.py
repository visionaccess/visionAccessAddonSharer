# -*- coding: UTF-8 -*-
# VisionAccess Add-on Sharer
# Package installed NVDA add-ons back into .nvda-addon files to back them up or share them.
# Copyright (C) 2026 Mukesh Jain, VisionAccess (www.visionaccess.org)
# Released under GNU General Public License version 2.

import os
import threading

import wx

import addonHandler
import config
import globalPluginHandler
import globalVars
import gui
import ui
from gui import guiHelper
from gui.nvdaControls import CustomCheckListBox
from logHandler import log
from scriptHandler import script

from . import packer

addonHandler.initTranslation()

CONFIG_SECTION = "visionAccessAddonSharer"
config.conf.spec[CONFIG_SECTION] = {
	"outputDir": "string(default='')",
	"openFolderWhenDone": "boolean(default=True)",
}


def defaultOutputDir():
	return os.path.join(os.path.expanduser("~"), "Documents", "NVDA Add-on Packages")


def getOutputDir():
	path = config.conf[CONFIG_SECTION]["outputDir"]
	return path if path else defaultOutputDir()


def getShareableAddons():
	"""Installed add-ons that still exist on disk, sorted by their display name."""
	addons = []
	for addon in addonHandler.getAvailableAddons():
		if getattr(addon, "isPendingRemove", False):
			continue
		if not os.path.isdir(addon.path):
			continue
		addons.append(addon)
	addons.sort(key=lambda a: (a.manifest.get("summary") or a.name).lower())
	return addons


def describeAddon(addon):
	summary = addon.manifest.get("summary") or addon.name
	# Translators: An item in the add-on list. {name} is the add-on name, {version} its version.
	text = _("{name}, version {version}").format(name=summary, version=addon.version)
	if getattr(addon, "isDisabled", False):
		# Translators: Added to an add-on in the list when that add-on is disabled.
		text += _(", disabled")
	return text


def copyFilesToClipboard(paths):
	"""Put files on the Windows clipboard so they can be pasted into Explorer, e-mail or WhatsApp."""
	data = wx.FileDataObject()
	for p in paths:
		data.AddFile(p)
	if not wx.TheClipboard.Open():
		return False
	try:
		wx.TheClipboard.SetData(data)
		wx.TheClipboard.Flush()
	finally:
		wx.TheClipboard.Close()
	return True


class SharerDialog(wx.Dialog):

	_instance = None

	def __init__(self, parent):
		# Translators: Title of the main window.
		super().__init__(parent, title=_("VisionAccess Add-on Sharer"))
		self.addons = getShareableAddons()
		self.outputDir = getOutputDir()
		self._busy = False

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		helper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)

		# Translators: Label of the list of installed add-ons.
		self.addonList = helper.addLabeledControl(
			_("&Installed add-ons (press space to check the ones you want to share):"),
			CustomCheckListBox,
			choices=[describeAddon(a) for a in self.addons],
		)
		self.addonList.SetMinSize((500, 300))
		if self.addons:
			self.addonList.SetSelection(0)

		selButtons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: Button that checks every add-on in the list.
		self.selectAllBtn = selButtons.addButton(self, label=_("Check &all"))
		# Translators: Button that unchecks every add-on in the list.
		self.clearBtn = selButtons.addButton(self, label=_("&Uncheck all"))
		helper.addItem(selButtons)

		# Translators: Label of the read-only field showing where packages will be saved.
		self.folderField = helper.addLabeledControl(
			_("Save packages in &folder:"),
			wx.TextCtrl,
			value=self.outputDir,
			style=wx.TE_READONLY,
		)
		# Translators: Button to choose the output folder.
		self.browseBtn = helper.addItem(wx.Button(self, label=_("&Browse...")))

		# Translators: Check box to open the output folder after packaging.
		self.openFolderCheck = helper.addItem(wx.CheckBox(self, label=_("&Open the folder when finished")))
		self.openFolderCheck.SetValue(config.conf[CONFIG_SECTION]["openFolderWhenDone"])

		# NVDA's addLabeledControl does not support wx.Gauge, so the label and bar are built by hand.
		progressSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Label of the progress bar.
		progressLabel = wx.StaticText(self, label=_("Progress:"))
		self.progress = wx.Gauge(self, range=100, size=(300, -1))
		self.progress.SetName(_("Progress:").rstrip(":"))
		progressSizer.Add(progressLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		progressSizer.AddSpacer(guiHelper.SPACE_BETWEEN_ASSOCIATED_CONTROL_HORIZONTAL)
		progressSizer.Add(self.progress, proportion=1)
		helper.addItem(progressSizer)

		actionButtons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: Button that creates the packages.
		self.packBtn = actionButtons.addButton(self, label=_("&Create packages"))
		# Translators: Button that closes the window.
		self.closeBtn = actionButtons.addButton(self, id=wx.ID_CLOSE, label=_("C&lose"))
		helper.addDialogDismissButtons(actionButtons)

		mainSizer.Add(helper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(mainSizer)
		mainSizer.Fit(self)
		self.CentreOnScreen()
		self.SetEscapeId(wx.ID_CLOSE)
		self.packBtn.SetDefault()

		self.selectAllBtn.Bind(wx.EVT_BUTTON, lambda e: self._checkAll(True))
		self.clearBtn.Bind(wx.EVT_BUTTON, lambda e: self._checkAll(False))
		self.browseBtn.Bind(wx.EVT_BUTTON, self.onBrowse)
		self.packBtn.Bind(wx.EVT_BUTTON, self.onPack)
		self.closeBtn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.addonList.SetFocus()

	def _checkAll(self, state):
		self.addonList.SetCheckedItems(range(len(self.addons)) if state else [])
		if state:
			# Translators: Spoken after checking all add-ons. {n} is how many.
			ui.message(_("{n} add-ons checked").format(n=len(self.addons)))
		else:
			# Translators: Spoken after unchecking all add-ons.
			ui.message(_("All add-ons unchecked"))
		self.addonList.SetFocus()

	def onBrowse(self, evt):
		# Translators: Title of the folder selection window.
		with wx.DirDialog(self, _("Choose where to save the add-on packages"), defaultPath=self.outputDir) as d:
			if d.ShowModal() == wx.ID_OK:
				self.outputDir = d.GetPath()
				self.folderField.SetValue(self.outputDir)
				config.conf[CONFIG_SECTION]["outputDir"] = self.outputDir

	def onPack(self, evt):
		if self._busy:
			return
		checked = list(self.addonList.GetCheckedItems())
		if not checked:
			gui.messageBox(
				# Translators: Shown when no add-on is checked.
				_("Please check at least one add-on in the list first. Use the space bar to check an add-on."),
				# Translators: Title of a message box.
				_("No add-on selected"),
				wx.OK | wx.ICON_INFORMATION, self,
			)
			self.addonList.SetFocus()
			return
		try:
			os.makedirs(self.outputDir, exist_ok=True)
		except OSError as e:
			gui.messageBox(
				# Translators: Shown when the output folder cannot be created.
				_("The folder {path} could not be created:\n{error}\nPlease choose another folder.").format(
					path=self.outputDir, error=e),
				_("Error"), wx.OK | wx.ICON_ERROR, self,
			)
			return
		config.conf[CONFIG_SECTION]["openFolderWhenDone"] = self.openFolderCheck.GetValue()
		selected = [self.addons[i] for i in checked]
		self._setBusy(True)
		self.progress.SetValue(0)
		# Translators: Spoken when packaging starts. {n} is the number of add-ons.
		ui.message(_("Packaging {n} add-ons, please wait").format(n=len(selected)))
		threading.Thread(target=self._worker, args=(selected, self.outputDir), daemon=True).start()

	def _setBusy(self, busy):
		self._busy = busy
		for ctrl in (self.addonList, self.selectAllBtn, self.clearBtn, self.browseBtn,
				self.openFolderCheck, self.packBtn, self.closeBtn):
			ctrl.Enable(not busy)

	def _worker(self, addons, outDir):
		created, failed = [], []
		total = len(addons)
		for index, addon in enumerate(addons, 1):
			summary = addon.manifest.get("summary") or addon.name
			dest = os.path.join(outDir, packer.packageFileName(addon.name, addon.version))
			try:
				packer.packAddon(addon.path, dest)
				created.append(dest)
			except Exception as e:
				log.error("Add-on Sharer could not package %s" % addon.name, exc_info=True)
				failed.append("%s: %s" % (summary, e))
			wx.CallAfter(self._onProgress, int(index * 100 / total))
		wx.CallAfter(self._onFinished, created, failed, outDir)

	def _onProgress(self, percent):
		if self:
			self.progress.SetValue(percent)

	def _onFinished(self, created, failed, outDir):
		if not self:
			return
		self._setBusy(False)
		# Translators: Result summary. {n} is the number of packages created, {path} the folder.
		msg = _("{n} add-on packages were created in:\n{path}").format(n=len(created), path=outDir)
		if failed:
			# Translators: Added to the result summary when some add-ons failed.
			msg += "\n\n" + _("These add-ons could not be packaged:") + "\n" + "\n".join(failed)
		if created:
			# Translators: Question at the end of the result summary.
			msg += "\n\n" + _("Do you want to copy the new files to the clipboard, so you can paste them into an e-mail, WhatsApp or a USB drive?")
			dlg = wx.MessageDialog(self, msg, _("Packaging finished"), wx.YES_NO | wx.ICON_INFORMATION)
			# Translators: Buttons of the result window.
			dlg.SetYesNoLabels(_("&Copy files to clipboard"), _("&No, thanks"))
			answer = dlg.ShowModal()
			dlg.Destroy()
			if answer == wx.ID_YES:
				if copyFilesToClipboard(created):
					# Translators: Spoken after files were copied.
					ui.message(_("Files copied. You can now paste them where you want."))
				else:
					ui.message(_("Could not open the clipboard."))
			if self.openFolderCheck.GetValue():
				try:
					os.startfile(outDir)
				except OSError:
					log.debugWarning("Could not open folder %s" % outDir, exc_info=True)
		else:
			gui.messageBox(msg, _("Packaging failed"), wx.OK | wx.ICON_ERROR, self)
		self.progress.SetValue(0)
		self.addonList.SetFocus()

	def onClose(self, evt):
		if self._busy:
			# Translators: Spoken if the user tries to close while packaging.
			ui.message(_("Please wait, packaging is still in progress"))
			if evt.CanVeto():
				evt.Veto()
				return
		SharerDialog._instance = None
		self.Destroy()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.menuItem = None
		if globalVars.appArgs.secure:
			return
		toolsMenu = gui.mainFrame.sysTrayIcon.toolsMenu
		# Translators: Item in the NVDA Tools menu.
		self.menuItem = toolsMenu.Append(wx.ID_ANY, _("VisionAccess &Add-on Sharer..."))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onOpen, self.menuItem)

	def terminate(self):
		try:
			if self.menuItem:
				gui.mainFrame.sysTrayIcon.toolsMenu.Remove(self.menuItem)
		except Exception:
			pass
		dlg = SharerDialog._instance
		if dlg:
			try:
				dlg.Destroy()
			except RuntimeError:
				pass
		super().terminate()

	def onOpen(self, evt=None):
		if globalVars.appArgs.secure:
			return
		dlg = SharerDialog._instance
		if dlg:
			try:
				if dlg.IsShown():
					dlg.Raise()
					dlg.addonList.SetFocus()
					return
			except RuntimeError:
				pass  # The window was already destroyed.
			SharerDialog._instance = None
		gui.mainFrame.prePopup()
		try:
			dlg = SharerDialog(gui.mainFrame)
			SharerDialog._instance = dlg
			dlg.Show()
			dlg.Raise()
		except Exception:
			log.error("VisionAccess Add-on Sharer could not open its window", exc_info=True)
			# Translators: Spoken if the window cannot open.
			ui.message(_("Add-on Sharer could not open. Please send the NVDA log to VisionAccess."))
		finally:
			gui.mainFrame.postPopup()

	@script(
		# Translators: Description of the command in Input Gestures.
		description=_("Opens the VisionAccess Add-on Sharer window"),
		# Translators: Category in Input Gestures.
		category=_("VisionAccess Add-on Sharer"),
		gesture="kb:NVDA+shift+alt+a",
	)
	def script_openSharer(self, gesture):
		wx.CallAfter(self.onOpen)
