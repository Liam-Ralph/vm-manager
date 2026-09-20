#!/usr/bin/env python3

# Copyright (C) 2026 Liam Ralph
# https://github.com/liam-ralph

# This program, including this file, is licensed under the MIT/Expat license.
# See LICENSE or this project's source for more information.
# Project source: https://github.com/liam-ralph/vm-manager

# VM Manager, an application for managing copies of virtual machines.


# Imports

# Standard Library

import ctypes
import enum
import importlib
import os
import shutil
import sys

# Third Party

import paramiko

# PySide6

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QErrorMessage,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QTextBrowser,
    QVBoxLayout,
    QWidget
)
from PySide6.QtCore import QObject, QSize, Qt, QThread, Signal
from PySide6.QtGui import QIcon, QPalette, QPixmap


# Global Variables

RELEASE_PATHS = False

if RELEASE_PATHS:
    PATH_LOGO = "/usr/share/icons/hicolor/512x512/apps/vm-manager.png"
    PATH_DOC = "/usr/share/doc/vm-manager"
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home != None:
        PATH_SETTINGS = os.path.expanduser(xdg_config_home + "/vm-manager/vm-manager.conf")
        PATH_VMS_CONF = os.path.expanduser(xdg_config_home + "/vm-manager/vms.conf")
    else:
        PATH_SETTINGS = os.path.expanduser("~/.config/vm-manager/vm-manager.conf")
        PATH_VMS_CONF = os.path.expanduser("~/.config/vm-manager/vms.conf")
    PATH_DEFAULT_SETTINGS = "/usr/share/vm-manager/defaults.conf"
    PATH_SCRIPTS = "/usr/share/vm-manager/scripts"
    PATH_ICONS = "/usr/share/vm-manager/icons"
else:
    # Assuming relative to project root, not /src
    PATH_LOGO = os.path.abspath("logo.png")
    PATH_DOC = os.path.abspath("")
    PATH_SETTINGS = os.path.abspath("conf/vm-manager/vm-manager.conf")
    PATH_VMS_CONF = os.path.abspath("conf/vm-manager/vms.conf")
    PATH_DEFAULT_SETTINGS = os.path.abspath("conf/defaults.conf")
    PATH_SCRIPTS = os.path.abspath("src")
    PATH_ICONS = os.path.abspath("icons")

PATH_README = PATH_DOC + "/README.md"
PATH_LICENSE = PATH_DOC + "/LICENSE"
PATH_SERVER_SCRIPTS = "~/.local/share/vm-manager"

with open(PATH_DOC + "/README.md", "r") as file:
    for i in range(2):
        file.readline()
    VERSION = file.readline()[12:]

SSH_AUTH_METHODS = ("Password", "Loaded Key", "Public Key", "Private Key")
SSH_KEY_TYPES = ("RSA", "ECDSA", "Ed25519")

ICON_NAMES = {
    "debian": ["debian", "ubuntu"],

}

icons_dict = {}


# Enums

class SSH_AUTH_METHOD(enum.IntEnum):
    PASSWORD = 0
    LOADED_KEY = 1
    PUBLIC_KEY = 2
    PRIVATE_KEY = 3

class LOAD_VALUE(enum.IntEnum):
    LOCAL = 0
    REMOTE = 1
    BOTH = 2


# Classes

# Virtual Machine

class VirtualMachine:

    def __init__(
        self, path, icon, local_size = None, server_size = None, local_md5 = None, server_md5 = None
    ):
        self.name = os.path.basename(path)
        self.path = path
        self.icon = icon
        self.local_size = local_size
        self.server_size = server_size
        self.local_md5 = local_md5
        self.server_md5 = server_md5
        self.widget = None

    def md5_match(self):
        if self.local_md5 is None or self.server_md5 is None:
            return False
        return self.local_md5 == self.server_md5

# Worker

class Worker(QObject):

    finished = Signal()
    warning_signal = Signal(tuple)

    # Constructor

    def __init__(self, MainWindow, vm = None):
        self.MainWindow = MainWindow
        self.vm = vm
        super().__init__()

    # Functions

    def load_vms(self):
        self.MainWindow.ssh_thread.wait()
        self.MainWindow.load_vms()
        self.finished.emit()

    def connect_ssh(self):
        try:
            self.MainWindow.connect_ssh()
        except Exception as e:
            self.warning_signal.emit(("Error Connecting to SSH", str(e)))
            self.MainWindow.ssh = None
        finally:
            self.finished.emit()

    def pull_vm(self):
        self.MainWindow.ssh_thread.wait()
        self.MainWindow.pull_vm(self.vm)
        self.finished.emit()

# Info Window

class InfoWindow(QMainWindow):

    # Class Variables

    def get_project_info():
        with open(PATH_README, "r") as file:
            return (
                file.readline()[2:] + "\n" + 
                file.readline()[3:] + "\n" +
                file.readline()[3:]
            )
    project_info = get_project_info()

    # Constructor

    def __init__(self, parent):

        super().__init__(parent)

        # Setup Info Window

        self.setWindowTitle("VM Manager Info")

        # Create Window

        self.window = QWidget()
        self.layout_back = QVBoxLayout(self.window)
        self.setCentralWidget(self.window)

        # Project Info

        self.project_info_label = QLabel(self.project_info)
        self.project_info_label.setWordWrap(True)
        self.project_info_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.project_info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.layout_back.addWidget(self.project_info_label)

        # License

        self.license_title = QLabel("License")
        self.license_title.font().setUnderline(True)
        self.license_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.layout_back.addWidget(self.license_title)

        self.license_label = QLabel(
            "This project is licensed under the MIT/Expat License.<br>" +
            "This license can be found in the following locations:<br>" +
            f"<a href=\"{PATH_LICENSE}\">Local Copy</a><br>" +
            # May fail to open if PATH_LICENSE contains a space
            "<a href=\"https://github.com/liam-ralph/vm-manager/blob/main/LICENSE\">" +
            "GitHub Repo (Official)</a><br>" +
            "<a href=\"https://mit-license.org/\">MIT License Website</a><br>"
        )
        self.license_label.setTextFormat(Qt.TextFormat.RichText)
        self.license_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.license_label.setOpenExternalLinks(True)
        self.license_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.layout_back.addWidget(self.license_label)

        # Doc Viewer

        layout_buttons = QHBoxLayout()

        self.view_readme = QPushButton("View README.md")
        self.view_readme.setObjectName("view_readme")
        self.view_readme.clicked.connect(self.open_doc)
        layout_buttons.addWidget(self.view_readme)

        self.view_changelog = QPushButton("View CHANGELOG.md")
        self.view_changelog.setObjectName("view_changelog")
        self.view_changelog.clicked.connect(self.open_doc)
        layout_buttons.addWidget(self.view_changelog)

        self.view_license = QPushButton("View LICENSE")
        self.view_license.setObjectName("view_license")
        self.view_license.clicked.connect(self.open_doc)
        layout_buttons.addWidget(self.view_license)

        self.layout_back.addLayout(layout_buttons)

        self.doc_viewer = QTextBrowser()
        self.doc_viewer.setReadOnly(True)
        self.doc_viewer.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.doc_viewer.setOpenExternalLinks(True)
        self.doc_viewer.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.layout_back.addWidget(self.doc_viewer)

    # Functions

    def open_doc(self):

        self.showMaximized()

        button = self.sender()
        contents = ""

        # Read and Display Documentation File

        if button.objectName() == "view_readme":
            with open(PATH_README, "r") as file:
                contents = file.read()
            self.doc_viewer.setMarkdown(contents)
        elif button.objectName() == "view_changelog":
            with open(os.path.join(PATH_DOC, "CHANGELOG.md"), "r") as file:
                contents = file.read()
            self.doc_viewer.setMarkdown(contents)
        elif button.objectName() == "view_license":
            with open(PATH_LICENSE, "r") as file:
                contents = file.read()
            self.doc_viewer.setMarkdown("")
            self.doc_viewer.setText(contents)

# Bar

class Bar(QLabel):

    def __init__(self, name, size, max_width, max_size):

        super().__init__(f"{name}\n{format_size(size)}")

        self.size = size

        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setWordWrap(True)
        self.setFixedWidth(max(0, round(max_width * size / max_size) - 4))

# Main Window

class MainWindow(QMainWindow):

    # Signals

    load_vm_widgets_signal = Signal()
    warning_signal = Signal(str)
    raise_ssh_error_signal = Signal(str)
    load_vm_widget_signal = Signal(VirtualMachine, int)
    load_vms_signal = Signal()

    # Constructor

    def __init__(self):

        super().__init__()

        # Setup Main Window

        self.setWindowTitle("VM Manager")
        self.icon = QIcon()
        self.icon.addFile(PATH_LOGO)
        self.setWindowIcon(self.icon)
        self.showMaximized()
        self.setMinimumSize(800, 550)
        self.setStyleSheet("QScrollArea { border: none; } QListWidget { border: none; }")

        # Create Window

        self.window = QWidget()
        self.layout_back = QVBoxLayout(self.window)
        self.setCentralWidget(self.window)

        # Load Settings

        self.load_settings()

        # Top

        self.info_button = QPushButton("Info")
        self.info_button.clicked.connect(self.show_info)
        self.layout_back.addWidget(self.info_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Middle

        self.layout_middle = QHBoxLayout()

        # Left (Settings)

        self.layout_left_scrollarea = QScrollArea()
        self.layout_left_scrollarea.setMinimumWidth(200)
        self.layout_left_scrollarea.setMaximumWidth(350)
        self.layout_left_widget = QWidget()
        self.layout_left = QVBoxLayout(self.layout_left_widget)

        # SSH Authentication Settings

        self.layout_left.addWidget(QLabel("SSH Authentication"))

        self.layout_left.addWidget(QLabel("SSH Authentication Method"))
        self.ssh_auth_method_combo = QComboBox()
        self.ssh_auth_method_combo.addItems(SSH_AUTH_METHODS)
        self.ssh_auth_method_combo.setCurrentIndex(self.settings["ssh_auth_method"])
        self.layout_left.addWidget(self.ssh_auth_method_combo)

        self.layout_left.addWidget(QLabel("SSH Key Type"))
        self.ssh_key_type_combo = QComboBox()
        self.ssh_key_type_combo.addItems(SSH_KEY_TYPES)
        self.ssh_key_type_combo.setCurrentText(self.settings["ssh_key_type"])
        self.layout_left.addWidget(self.ssh_key_type_combo)

        self.layout_left.addWidget(QLabel("SSH Timeout (seconds)"))
        self.ssh_timeout_entry = QSlider(Qt.Orientation.Horizontal)
        self.ssh_timeout_entry.setMinimum(1)
        self.ssh_timeout_entry.setMaximum(60)
        self.ssh_timeout_entry.setValue(self.settings["ssh_timeout"])
        self.layout_left.addWidget(self.ssh_timeout_entry)
        self.ssh_timeout_label = QLabel(str(self.settings["ssh_timeout"]))
        self.layout_left.addWidget(self.ssh_timeout_label)

        # Server Address Settings

        self.layout_left.addSpacing(20)
        self.layout_left.addWidget(QLabel("Server Address"))

        self.layout_left.addWidget(QLabel("Server Hostname"))
        self.server_hostname_entry = QLineEdit()
        self.server_hostname_entry.setPlaceholderText(self.settings["server_hostname"])
        self.layout_left.addWidget(self.server_hostname_entry)

        self.layout_left.addWidget(QLabel("Server Username"))
        self.server_username_entry = QLineEdit()
        self.server_username_entry.setPlaceholderText(self.settings["server_username"])
        self.layout_left.addWidget(self.server_username_entry)

        # Virtual Machines Settings

        self.layout_left.addSpacing(20)
        self.layout_left.addWidget(QLabel("Virtual Machines"))

        self.layout_left.addWidget(QLabel("Local VMs Path"))
        self.local_vms_path_entry = QLineEdit()
        self.local_vms_path_entry.setPlaceholderText(self.settings["local_vms_path"])
        self.layout_left.addWidget(self.local_vms_path_entry)

        self.layout_left.addWidget(QLabel("Server VMs Path"))
        self.server_vms_path_entry = QLineEdit()
        self.server_vms_path_entry.setPlaceholderText(self.settings["server_vms_path"])
        self.layout_left.addWidget(self.server_vms_path_entry)

        self.layout_left.addWidget(QLabel("VM Extension"))
        self.vm_ext_entry = QLineEdit()
        self.vm_ext_entry.setPlaceholderText(self.settings["vm_ext"])
        self.layout_left.addWidget(self.vm_ext_entry)

        self.layout_left.addWidget(QLabel("VM Hashfile Path"))
        self.vm_hashfile_path_entry = QLineEdit()
        self.vm_hashfile_path_entry.setPlaceholderText(self.settings["vm_hashfile_path"])
        self.layout_left.addWidget(self.vm_hashfile_path_entry)

        self.layout_left.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_left_scrollarea.setWidget(self.layout_left_widget)
        self.layout_left_scrollarea.setWidgetResizable(True)
        self.layout_middle.addWidget(self.layout_left_scrollarea)

        # Center (VM Management)

        self.layout_center_widget = QWidget()

        self.layout_center = QVBoxLayout(self.layout_center_widget)

        # Title

        self.layout_center.addWidget(
            QLabel("Virtual Machine Management"), alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Manage All Virtual Machines

        self.layout_vm_buttons = QHBoxLayout()

        self.push_all_button = QPushButton("Push All")
        self.layout_vm_buttons.addWidget(self.push_all_button)

        self.pull_all_button = QPushButton("Pull All")
        self.layout_vm_buttons.addWidget(self.pull_all_button)

        self.update_all_button = QPushButton("Update All")
        self.layout_vm_buttons.addWidget(self.update_all_button)

        self.layout_center.addLayout(self.layout_vm_buttons)

        # Individual Machines

        self.layout_center_listwidget = QListWidget()
        self.layout_center_listwidget.setMinimumWidth(400)
        self.layout_center_listwidget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.layout_center_listwidget.viewport().setBackgroundRole(QPalette.Window)
        self.layout_center_listwidget.setFlow(QListWidget.Flow.LeftToRight)
        self.layout_center_listwidget.setWrapping(True)
        self.layout_center_listwidget.setMovement(QListWidget.Movement.Static)
        self.layout_center_listwidget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.layout_center_listwidget.setHorizontalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.layout_center_listwidget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.layout_center_listwidget.setSpacing(5)
        self.layout_center.addWidget(self.layout_center_listwidget)

        self.layout_middle.addWidget(self.layout_center_widget)

        # Right (VM Sizes)

        self.layout_right_widget = QScrollArea()
        self.layout_right_widget.setWidgetResizable(True)
        self.layout_right_widget.setMinimumWidth(200)
        self.layout_right_widget.setMaximumWidth(400)
        self.layout_right_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.layout_right_content = QWidget()
        self.layout_right = QVBoxLayout(self.layout_right_content)
        self.layout_right.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.layout_right_widget.setWidget(self.layout_right_content)

        self.layout_right.addWidget(
            QLabel("Virtual Machine Sizes", alignment=Qt.AlignmentFlag.AlignCenter)
        )

        # Local

        self.layout_right.addWidget(QLabel("Local", alignment=Qt.AlignmentFlag.AlignCenter))

        self.layout_right_local_widget = QWidget()
        self.layout_right_local = QVBoxLayout(self.layout_right_local_widget)
        self.layout_right.addWidget(self.layout_right_local_widget)

        # Server

        self.layout_right.addWidget(QLabel("Remote", alignment=Qt.AlignmentFlag.AlignCenter))

        self.layout_right_server_widget = QWidget()
        self.layout_right_server = QVBoxLayout(self.layout_right_server_widget)
        self.layout_right.addWidget(self.layout_right_server_widget)

        self.layout_middle.addWidget(self.layout_right_widget)

        self.layout_back.addLayout(self.layout_middle)

        # Connect Signals

        self.warning_signal.connect(self.show_warning)
        self.raise_ssh_error_signal.connect(self.raise_ssh_error)
        self.load_vms_signal.connect(self.start_load_vms)
        self.load_vm_widgets_signal.connect(self.load_vm_widgets)
        self.load_vm_widget_signal.connect(
            lambda vm, load_value: self.load_vm_widget(vm, load_value)
        )

        self.ssh = None
        self.start_load_vms()

    # Destructor

    def __del__(self):

        # Clear Password

        self.clear_password()

        # Close SSH

        try:
            if self.ssh is not None:
                self.ssh.close()
        except (RuntimeError, AttributeError):
            pass

        # Quit QThreads

        try:
            if self.vm_thread is not None and self.vm_thread.isRunning():
                self.vm_thread.quit()
                self.vm_thread.wait()
        except (RuntimeError, AttributeError):
            pass

        try:
            if self.ssh_thread is not None and self.ssh_thread.isRunning():
                self.ssh_thread.quit()
                self.ssh_thread.wait()
        except (RuntimeError, AttributeError):
            pass

    # Functions

    def start_load_vms(self):

        # Connect SSH

        if self.ssh is None:
            self.start_connect_ssh()

        # Load Virtual Machines

        self.vm_thread = QThread()
        self.vm_worker = Worker(self)
        self.vm_worker.moveToThread(self.vm_thread)
        self.vm_thread.started.connect(self.vm_worker.load_vms)
        self.vm_worker.warning_signal.connect(self.show_warning)
        self.vm_worker.finished.connect(self.vm_thread.quit)
        self.vm_thread.finished.connect(self.vm_worker.deleteLater)
        self.vm_thread.finished.connect(self.load_vm_widgets_signal.emit)
        self.vm_thread.start()

    def start_connect_ssh(self):

        # Settings Check

        missing_settings = []
        for setting in (
            "server_hostname", "server_username",
            "local_vms_path", "server_vms_path", "vm_ext", "vm_hashfile_path"
        ):
            if setting not in self.settings.keys():
                missing_settings.append(setting)
        if (
            self.settings["ssh_auth_method"] in
            (SSH_AUTH_METHOD.PRIVATE_KEY, SSH_AUTH_METHOD.PUBLIC_KEY) and
            self.settings["key_path"] == ""
        ):
            missing_settings.append("key_path")

        if len(missing_settings) > 0:
            self.warning_signal.emit("Missing settings: " + ", ".join(missing_settings))
            return

        # Get Password

        self.clear_password()
        if (
            self.settings["ssh_auth_method"] in
            (SSH_AUTH_METHOD.PASSWORD, SSH_AUTH_METHOD.PRIVATE_KEY)
        ):
            input_dialog = QInputDialog(self)
            input_dialog.setWindowTitle(
                "SSH " + (
                    "Key " if self.settings["ssh_auth_method"] == SSH_AUTH_METHOD.PRIVATE_KEY
                    else ""
                ) + "Password"
            )
            input_dialog.setLabelText("Enter Password")
            input_dialog.setInputMode(QInputDialog.TextInput)
            input_dialog.setTextEchoMode(QLineEdit.Password)
            input_dialog.resize(300, 200)
            ok = input_dialog.exec()
            if ok:
                self.saved_password = input_dialog.textValue()
            else:
                self.saved_password = None

        # Connect SSH

        self.ssh_thread = QThread()
        self.ssh_worker = Worker(self)
        self.ssh_worker.moveToThread(self.ssh_thread)
        self.ssh_thread.started.connect(self.ssh_worker.connect_ssh)
        self.ssh_worker.warning_signal.connect(self.show_warning)
        self.ssh_worker.finished.connect(self.ssh_thread.quit)
        self.ssh_thread.finished.connect(self.ssh_worker.deleteLater)
        self.ssh_thread.start()

    def load_vms(self):

        # Load Virtual Machines Config

        global icons_dict
        if os.path.exists(PATH_VMS_CONF):
            with open(PATH_VMS_CONF, "r") as file:
                for line in file:
                    name, icon = line.split(" / ")
                    icons_dict[name] = icon

        # Get Local VMs

        self.vms = []

        spec = importlib.util.spec_from_file_location(
            "get-machines", PATH_SCRIPTS + "/get-machines.py"
        )
        get_machines = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(get_machines)
        vms_str = get_machines.get_machines(
            self.settings["local_vms_path"], self.settings["vm_ext"],
            self.settings["vm_hashfile_path"]
        )
        for line in vms_str.splitlines():
            if len(line) < 34:
                print(line)
                continue
            md5_hash = line[:32]
            line = line[33:]
            size, path = line.split(" ", 1)
            self.vms.append(VirtualMachine(
                path, self.get_icon(self.settings["local_vms_path"], path),
                local_size=int(size), local_md5=md5_hash
            ))

        # Get Server VMs

        if self.ssh is not None:

            stdout = self.ssh_exec_command(
                f"/usr/bin/python3 {PATH_SERVER_SCRIPTS}/get-machines.py " +
                f"\"{self.settings["server_vms_path"]}\" \"{self.settings["vm_ext"]}\" " +
                f"\"{self.settings["vm_hashfile_path"]}\""
            )

            for line in stdout.splitlines():
                line = line.decode()
                if len(line) < 34:
                    print(line)
                    continue
                md5_hash = line[:32]
                line = line[33:]
                size, path = line.split(" ", 1)
                found_vm = False
                for vm in self.vms:
                    if vm.path == path:
                        vm.server_size = int(size)
                        vm.server_md5 = md5_hash
                        found_vm = True
                        break
                if not found_vm:
                    self.vms.append(VirtualMachine(
                        path, self.get_icon(self.settings["server_vms_path"], path),
                        server_size=int(size), local_md5=md5_hash
                    ))

        self.vms = sorted(self.vms, key=lambda vm: vm.path.lower())

    def clear_password(self):

        try:
            ctypes.memset(id(self.saved_password) + 20, 0, sys.getsizeof(self.saved_password))
        except AttributeError:
            pass
        self.saved_password = None

    def show_warning(self, warning_str):

        QMessageBox.warning(self, warning_str[0], warning_str[1])

    def load_vm_widgets(self):

        # Set Sizes Bar Colors

        self.layout_right_local_widget.setStyleSheet(
            "QLabel { border: 2px solid; margin: 1px; padding: 1px; }"
        )
        self.layout_right_server_widget.setStyleSheet(
            "QLabel { border: 2px solid; margin: 1px; padding: 1px; }"
        )

        # Get Virtual Machine Maximum Size

        max_width = self.layout_right_local_widget.width() - 20
        max_size = 1
        for vm in self.vms:
            if vm.local_size is not None and vm.local_size > max_size:
                max_size = vm.local_size
            if vm.server_size is not None and vm.server_size > max_size:
                max_size = vm.server_size

        # Size Widget Lists

        local_bars = []
        server_bars = []

        # Display Virtual Machines

        for vm in self.vms:

            # Add to Center ListWidget

            vm.widget = QWidget()
            vm.widget.setFixedSize(350, 200)
            vm.widget.setObjectName("vm_widget")
            vm.widget.setStyleSheet("QWidget#vm_widget { border: 2px solid; }")
            vm.layout_back = QVBoxLayout(vm.widget)

            # Top

            vm.layout_top = QHBoxLayout()

            vm.layout_top.addWidget(QLabel(vm.name))

            vm.md5_label = QLabel(
                "Local =" + ("=" if vm.md5_match() else "/") + "= Remote"
            )
            vm.layout_top.addWidget(vm.md5_label)

            vm.layout_back.addLayout(vm.layout_top)

            # Bottom

            vm.layout_bottom = QHBoxLayout()

            # Icon

            vm.layout_icon = QVBoxLayout()

            vm.pixmap = QPixmap(os.path.join(PATH_ICONS, vm.icon))
            vm.pixmap_scaled = vm.pixmap.scaled(100, 100)
            vm.icon_label = QLabel()
            vm.icon_label.setPixmap(vm.pixmap_scaled)
            vm.layout_icon.addWidget(vm.icon_label)

            vm.change_icon_button = QPushButton("Change Icon")
            vm.change_icon_button.setFixedWidth(100)
            vm.layout_icon.addWidget(vm.change_icon_button)

            vm.layout_bottom.addLayout(vm.layout_icon)

            # Local State

            vm.layout_local = QVBoxLayout()

            vm.layout_local.addWidget(QLabel("Local"))

            vm.local_size_label = QLabel(format_size(vm.local_size))
            vm.layout_local.addWidget(vm.local_size_label)

            vm.push_button = QPushButton("Push")
            if vm.local_size is None:
                vm.push_button.setEnabled(False)
            vm.layout_local.addWidget(vm.push_button)

            vm.local_delete_button = QPushButton("Delete")
            if vm.local_size is None:
                vm.local_delete_button.setEnabled(False)
            vm.layout_local.addWidget(vm.local_delete_button)

            vm.local_update_button = QPushButton("Update")
            vm.layout_local.addWidget(vm.local_update_button)

            vm.layout_bottom.addLayout(vm.layout_local)

            # Server State

            vm.layout_server = QVBoxLayout()

            vm.layout_server.addWidget(QLabel("Remote"))

            vm.server_size_label = QLabel(format_size(vm.server_size))
            vm.layout_server.addWidget(vm.server_size_label)

            vm.pull_button = QPushButton("Pull")
            if vm.server_size is None:
                vm.pull_button.setEnabled(False)
            vm.pull_button.pressed.connect(lambda vm=vm: self.start_pull_vm(vm))
            vm.layout_server.addWidget(vm.pull_button)

            vm.server_delete_button = QPushButton("Delete")
            if vm.server_size is None:
                vm.server_delete_button.setEnabled(False)
            vm.layout_server.addWidget(vm.server_delete_button)

            vm.server_update_button = QPushButton("Update")
            vm.layout_server.addWidget(vm.server_update_button)

            vm.layout_bottom.addLayout(vm.layout_server)

            vm.layout_back.addLayout(vm.layout_bottom)

            # Add Widget to ListWidget

            vm.widget.setParent(self.layout_center_listwidget)
            item = QListWidgetItem()
            item.setFlags(item.flags() & ~(Qt.ItemIsSelectable|Qt.ItemIsEnabled))
            self.layout_center_listwidget.addItem(item)
            item.setSizeHint(QSize(350, 200))
            self.layout_center_listwidget.setItemWidget(item, vm.widget)

            # Add To Virtual Machine Sizes

            # Local

            if vm.local_size is not None:
                local_bars.append(Bar(vm.name,vm.local_size, max_width, max_size))

            # Server

            if vm.server_size is not None:
                server_bars.append(Bar(vm.name, vm.server_size, max_width, max_size))

        # Sort and Add Bars

        for bar in sorted(local_bars, key=lambda b: b.size, reverse=True):
            self.layout_right_local.addWidget(bar)
        for bar in sorted(server_bars, key=lambda b: b.size, reverse=True):
            self.layout_right_server.addWidget(bar)

    def raise_ssh_error(self, err):
        error_message = QErrorMessage(self)
        error_message.showMessage(err)
        raise ValueError(err)

    def load_settings(self):
        """
        Load user settings from `PATH_SETTINGS`.

        :return: An instance of the `Settings` class containing the loaded settings.
        """

        self.settings = {}

        if not os.path.exists(PATH_SETTINGS):
            settings_dir = os.path.dirname(PATH_SETTINGS)
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
            shutil.copy(PATH_DEFAULT_SETTINGS, PATH_SETTINGS)

        with open(PATH_SETTINGS, "r") as file:
            for line in file:

                if line[0] in ("#", "\n"):
                    continue

                line = line.strip()
                if line.endswith("="):
                    self.settings[line[:-1]] = ""
                    continue
                setting, value = line.split("=")

                if setting in ("ssh_auth_method", "ssh_timeout"):
                    value = int(value)
                self.settings[setting] = value

        for setting in (
            "ssh_auth_method", "ssh_key_type", "ssh_timeout",
            "server_hostname", "server_username", "local_vms_path", "server_vms_path",
            "vm_ext", "vm_hashfile_path"
        ):
            if setting not in self.settings.keys():
                self.raise_ssh_error("Missing setting: " + setting)

    def set_setting(self, setting, value):
        """
        Set user setting in `PATH_SETTINGS`.

        :param setting: The setting to set.
        :param value: The value to set `setting` to.
        """

        if not os.path.exists(PATH_SETTINGS) and RELEASE_PATHS:
            settings_dir = os.path.dirname(PATH_SETTINGS)
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
            shutil.copy(PATH_DEFAULT_SETTINGS, PATH_SETTINGS)

        with open(PATH_SETTINGS, "r+") as file:
            pass

        self.settings[setting] = value

    def show_info(self):
        """Open the info window."""
        info_window = InfoWindow(self)
        info_window.show()

    def connect_ssh(self):

        self.ssh = paramiko.SSHClient()

        password = None
        pkey = None

        # Password Connection

        if self.settings["ssh_auth_method"] == SSH_AUTH_METHOD.PASSWORD:
            if self.saved_password is None:
                raise ValueError("Auth type is password and no password given.")
            password = self.saved_password

        # Key Connection

        elif self.settings["ssh_auth_method"] == SSH_AUTH_METHOD.LOADED_KEY:
            self.ssh.load_system_host_keys()
            self.ssh.set_missing_host_key_policy(paramiko.RejectPolicy())

        else:
            if (
                self.settings["ssh_auth_method"] == SSH_AUTH_METHOD.PRIVATE_KEY and
                self.saved_password is None
            ):
                raise ValueError("Auth type requires password and no password given.")
            if self.settings["ssh_key_type"] == "RSA":
                key = paramiko.RSAKey.from_private_key_file(
                    self.settings["ssh_key_path"], self.saved_password
                )
            elif self.settings["ssh_key_type"] == "ECDSA":
                key = paramiko.ECDSAKey.from_private_key_file(
                    self.settings["ssh_key_path"], self.saved_password
                )
            else:
                key = paramiko.Ed25519Key.from_private_key_file(
                    self.settings["ssh_key_path"], self.saved_password
                )
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            pkey = key

        self.ssh.connect(
            hostname=self.settings["server_hostname"], username=self.settings["server_username"],
            password=password, pkey=pkey,
            timeout=self.settings["ssh_timeout"], banner_timeout=self.settings["ssh_timeout"],
            auth_timeout=self.settings["ssh_timeout"]
        )

        # Install Any Missing Scripts

        if not self.ssh_path_found(PATH_SERVER_SCRIPTS, "d"):
            self.ssh_exec_command("mkdir -p " + PATH_SERVER_SCRIPTS)

        sftp = self.ssh.open_sftp()

        for script in os.listdir(PATH_SCRIPTS):
            local_path = os.path.join(PATH_SCRIPTS, script)
            if (
                (not os.path.isfile(local_path)) or
                ((not RELEASE_PATHS) and script.endswith(os.path.basename(__file__)))
            ):
                continue
            server_path = (
                os.path.join(PATH_SERVER_SCRIPTS, script).replace(
                    "~", "/home/" + self.settings["server_username"], 1
                )
            )
            if not self.ssh_path_found(server_path):
                sftp.put(local_path, server_path)

        sftp.close()

    def ssh_path_found(self, path, type = "e"):
        if path[0] == "~":
            path = path.replace("~", "/home/" + self.settings["server_username"], 1)
        return b"found" in self.ssh_exec_command(f"if [ -{type} \"{path}\" ]; then echo found; fi")

    def ssh_exec_command(self, command):
        stdout, stderr = self.ssh.exec_command(command)[1:]
        stderr_data = stderr.read()
        if stderr_data:
            self.raise_ssh_error_signal.emit(f"Error with ssh command \"{command}\": {stderr_data}")
        return stdout.read()

    def get_icon(self, vms_path, vm_path):

        # Check Saved Icons

        global icons_dict
        icon = icons_dict[vm_path] if vm_path in icons_dict.keys() else "unknown"

        if icon == "unknown":

            # Search Function

            def search_icon_names(target):
                nonlocal icon
                for key in ICON_NAMES.keys():
                    found = False
                    for assoc_name in ICON_NAMES[key]:
                        if assoc_name in target.lower():
                            icon = key
                            found = True
                            break
                    if found:
                        break

            # Compare with Name

            search_icon_names(vm_path)

            if icon == "unknown":

                # Look for OS Type

                os_type = None
                search_path = os.path.join(vms_path, vm_path)
                if os.path.exists(search_path):
                    for path in os.listdir(search_path):
                        if path.endswith(".vbox"):
                            with open(os.path.join(search_path, path), "r") as file:
                                for line in file.readlines():
                                    if line.strip().startswith("<Machine"):
                                        for word in line.strip().split(" "):
                                            if word.startswith("OSType="):
                                                os_type = word[7:].lower()
                                                break
                                        break
                            break

                # Compare with OS Type

                if os_type is not None:
                    search_icon_names(os_type)

        return icon + ".png"

    def load_vm_widget(self, vm: VirtualMachine, load_value):

        if load_value in (LOAD_VALUE.LOCAL, LOAD_VALUE.BOTH):
            spec = importlib.util.spec_from_file_location(
                "get-vm-info", PATH_SCRIPTS + "/get-vm-info.py"
            )
            get_vm_info = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(get_vm_info)
            vm_str = get_vm_info.get_vm_info(
                self.settings["local_vms_path"], vm.path, self.settings["vm_hashfile_path"]
            )
            if len(vm_str) > 34:
                vm.local_md5 = vm_str[:32]
                vm.local_size = int(vm_str[33:])
                vm.local_size_label.setText(format_size(vm.local_size))
                vm.push_button.setEnabled(True)
                vm.local_delete_button.setEnabled(True)
            else:
                print(vm_str)

        if load_value in (LOAD_VALUE.LOCAL, LOAD_VALUE.BOTH):
            stdout = self.ssh_exec_command(
                f"/usr/bin/python3 {PATH_SERVER_SCRIPTS}/get-vm-info.py " +
                f"\"{self.settings["server_vms_path"]}\" \"{vm.path}\" " +
                f"\"{self.settings["vm_hashfile_path"]}\""
            )
            vm_str = stdout.decode()
            if len(vm_str) > 34:
                vm.server_md5 = vm_str[:32]
                vm.server_size = int(vm_str[33:])
                vm.server_size_label.setText(format_size(vm.server_size))
                vm.pull_button.setEnabled(True)
                vm.server_delete_button.setEnabled(True)
            else:
                print(vm_str)

        vm.md5_label.setText("Local =" + ("=" if vm.md5_match() else "/") + "= Remote")

    def start_pull_vm(self, vm):

        # Connect SSH

        if self.ssh is None:
            self.start_connect_ssh()

        # Pull Virtual Machine

        self.vm_thread = QThread()
        self.vm_worker = Worker(self, vm)
        self.vm_worker.moveToThread(self.vm_thread)
        self.vm_thread.started.connect(self.vm_worker.pull_vm)
        self.vm_worker.warning_signal.connect(self.show_warning)
        self.vm_worker.finished.connect(self.vm_thread.quit)
        self.vm_thread.finished.connect(self.vm_worker.deleteLater)
        self.vm_thread.finished.connect(
            lambda: self.load_vm_widget_signal.emit(vm, LOAD_VALUE.LOCAL)
        )
        self.vm_thread.start()

    def pull_vm(self, vm):

        if self.ssh is None:
            self.start_connect_ssh()

        sftp = self.ssh.open_sftp()

        stdout = self.ssh_exec_command(
            f"/usr/bin/python3 {PATH_SERVER_SCRIPTS}/get-vm-files.py " +
            f"\"{self.settings["server_vms_path"]}\" \"{vm.path}\""
        )

        local_vm_path = os.path.join(self.settings["local_vms_path"], vm.path)
        if os.path.exists(local_vm_path):
            shutil.rmtree(local_vm_path, ignore_errors=True)

        for line in stdout.splitlines():
            line = line.decode()
            if len(line) < 4:
                continue
            type = line[:4]
            path = line[4:]
            local_path = os.path.join(self.settings["local_vms_path"], path)
            if type == "file":
                sftp.get(os.path.join(self.settings["server_vms_path"], path), local_path)
            elif type == "dir_":
                if not os.path.exists(local_path):
                    os.mkdir(local_path)

        sftp.close()

# Functions

def format_size(size):
    if size is None:
        return "Nonexistent"
    suffixes = ("B", "kiB", "MiB", "GiB", "TiB", "PiB", "EiB")
    exp = 0
    while (size >= pow(1024, exp + 1)):
        exp += 1
    return str(round(size / pow(1024, exp), 2)) + " " + suffixes[exp]


# Main Function

def main():
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()


# Run Main Function

if __name__ == "__main__":
    main()
