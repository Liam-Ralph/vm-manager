#!/usr/bin/env python3

# Copyright (C) 2026 Liam Ralph
# https://github.com/liam-ralph

# This program, including this file, is licensed under the MIT/Expat license.
# See LICENSE or this project's source for more information.
# Project source: https://github.com/liam-ralph/vm-manager

# VM Manager, an application for managing copies of virtual machines.


# Imports

# Standard Library

import importlib
import os
import shutil

# Third Party

import keyring
import paramiko

# PySide6

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QErrorMessage,
    QFrame,
    QHBoxLayout,
    QImage,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


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

PATH_SERVER_SCRIPTS = "~/.local/share/vm-manager"

with open(PATH_DOC + "/README.md", "r") as file:
    for i in range(2):
        file.readline()
    VERSION = file.readline()[12:]

SSH_AUTH_TYPES = ("Password", "Key")
SSH_KEY_TYPES = ("RSA", "ECDSA", "Ed25519")

ICON_NAMES = {
    "debian": ["debian", "ubuntu"],

}


# Classes

# Virtual Machine

class VirtualMachine:

    def __init__(self, name, icon, local_size = None, server_size = None):
        self.name = name
        self.icon = icon
        self.local_size = local_size
        self.server_size = server_size

# Info Window

class InfoWindow(QMainWindow):

    def __init__(self, parent):

        super().__init__(parent)

        # Setup Info Window

        self.setWindowTitle("VM Manager Info")

        # Create Window

        window = QWidget()
        layout_back = QVBoxLayout(window)
        self.setCentralWidget(window)

# Virtual Machine Widget

class VirtualMachineWidget(QWidget):

    # Constructor

    def __init__(self, vm, local):

        super().__init__()

        self.setFixedSize(600, 600)

        vm_size = vm.local_size if local else vm.server_size

        if vm_size is not None:

            layout_back = QVBoxLayout(self)
            layout_back.setAlignment(Qt.AlignmentFlag.AlignTop)

            # Virtual Machine Size

            layout_back.addWidget(QLabel(format_size(vm_size)))

            layout_bottom = QHBoxLayout()

            # Buttons

            buttons = QWidget()
            buttons.setFixedSize(200, 400)
            layout_buttons = QVBoxLayout(buttons)
            layout_buttons.setAlignment(Qt.AlignmentFlag.AlignTop)
            push_vm_button = QPushButton("Push")
            layout_buttons.addWidget(push_vm_button)
            pull_vm_button = QPushButton("Pull")
            layout_buttons.addWidget(pull_vm_button)
            remove_vm_button = QPushButton("Pull")
            layout_buttons.addWidget(remove_vm_button)
            layout_bottom.addWidget(buttons)

            # Virtual Machine Icon

            icon = QImage()
            icon.load(f"{PATH_ICONS}/{vm.icon}")
            icon.setFixedSize(400, 400)
            layout_bottom.addWidget(icon)

            layout_back.addLayout(layout_bottom)

        else:

            icon = QImage()
            icon.load(PATH_ICONS + "/missing.png")
            icon.setFixedSize(600, 600)
            self.addWidget(icon)

# Main Window

class MainWindow(QMainWindow):

    # Constructor

    def __init__(self):

        super().__init__()

        # Setup Main Window

        self.setWindowTitle("VM Manager")
        icon = QIcon()
        icon.addFile(PATH_LOGO)
        self.setWindowIcon(icon)
        self.showMaximized()
        self.setMinimumSize(800, 550)

        # Create Window

        window = QWidget()
        layout_back = QVBoxLayout(window)
        self.setCentralWidget(window)

        # Load Settings

        self.load_settings()

        # Top

        info_button = QPushButton("Info")
        info_button.clicked.connect(self.show_info)
        layout_back.addWidget(info_button)
        layout_back.setAlignment(info_button, Qt.AlignmentFlag.AlignRight)

        # Middle

        layout_middle = QHBoxLayout()

        # Left (Settings)

        layout_left_widget = QWidget()
        layout_left_widget.setMinimumWidth(200)
        layout_left_widget.setMaximumWidth(400)
        layout_left = QVBoxLayout(layout_left_widget)

        # SSH Authentication Settings

        layout_left.addWidget(QLabel("SSH Authentication"))

        ssh_auth_type_combo = QComboBox()
        ssh_auth_type_combo.addItems(SSH_AUTH_TYPES)
        ssh_auth_type_combo.setCurrentIndex(SSH_AUTH_TYPES.index(self.settings["ssh_auth_type"]))
        layout_left.addWidget(ssh_auth_type_combo)

        layout_left.addWidget(QLabel("SSH Key Path"))
        ssh_key_path_entry = QLineEdit()
        ssh_key_path_entry.setPlaceholderText(self.settings["ssh_key_path"])
        layout_left.addWidget(ssh_key_path_entry)

        ssh_key_type_combo = QComboBox()
        ssh_key_type_combo.addItems(SSH_KEY_TYPES)
        ssh_key_type_combo.setCurrentIndex(SSH_KEY_TYPES.index(self.settings["ssh_key_type"]))
        layout_left.addWidget(ssh_key_type_combo)

        ssh_key_encrypted_check = QCheckBox()
        ssh_key_encrypted_check.setChecked(self.settings["ssh_key_encrypted"])
        layout_left.addWidget(ssh_key_encrypted_check)

        save_ssh_password_check = QCheckBox("Save SSH Password")
        save_ssh_password_check.setChecked(self.settings["save_ssh_password"])
        layout_left.addWidget(save_ssh_password_check)

        if self.settings["save_ssh_password"]:
            save_ssh_password_button = QPushButton("Set Saved SSH Password")
            def save_ssh_password():
                password = self.get_password("SSH Password")
                if password is not None:
                    keyring.set_password("VM Manager", "SSH Password", password)
            save_ssh_password_button.clicked.connect(save_ssh_password)
            layout_left.addWidget(save_ssh_password_button)

        clear_ssh_password_button = QPushButton("Clear Saved SSH Password")
        clear_ssh_password_button.clicked.connect(
            lambda: keyring.delete_password("VM Manager", "SSH Password")
        )
        layout_left.addWidget(clear_ssh_password_button)

        save_ssh_key_password_check = QCheckBox("Save SSH Key Password")
        save_ssh_key_password_check.setChecked(self.settings["save_ssh_key_password"])
        layout_left.addWidget(save_ssh_key_password_check)

        if self.settings["save_ssh_key_password"]:
            save_ssh_key_password_button = QPushButton("Set Saved SSH Key Password")
            def save_ssh_key_password():
                password = self.get_password("SSH Key Password")
                if password is not None:
                    keyring.set_password("VM Manager", "SSH Key Password", password)
            save_ssh_key_password_button.clicked.connect(save_ssh_key_password)
            layout_left.addWidget(save_ssh_key_password_button)

        clear_ssh_key_password_button = QPushButton("Clear Saved SSH Key Password")
        clear_ssh_key_password_button.clicked.connect(
            lambda: keyring.delete_password("VM Manager", "SSH Key Password")
        )
        layout_left.addWidget(clear_ssh_key_password_button)

        # Server Address Settings

        layout_left.addSpacing(20)
        layout_left.addWidget(QLabel("Server Address"))

        layout_left.addWidget(QLabel("Server Hostname"))
        server_hostname_entry = QLineEdit()
        server_hostname_entry.setPlaceholderText(self.settings["server_hostname"])
        layout_left.addWidget(server_hostname_entry)

        layout_left.addWidget(QLabel("Server Username"))
        server_username_entry = QLineEdit()
        server_username_entry.setPlaceholderText(self.settings["server_username"])
        layout_left.addWidget(server_username_entry)

        # Virtual Machines Settings

        layout_left.addSpacing(20)
        layout_left.addWidget(QLabel("Virtual Machines"))

        local_vms_path_entry = QLineEdit()
        local_vms_path_entry.setPlaceholderText(self.settings["local_vms_path"])
        layout_left.addWidget(local_vms_path_entry)

        server_vms_path_entry = QLineEdit()
        server_vms_path_entry.setPlaceholderText(self.settings["server_vms_path"])
        layout_left.addWidget(server_vms_path_entry)

        vm_ext_entry = QLineEdit()
        vm_ext_entry.setPlaceholderText(self.settings["vm_ext"])
        layout_left.addWidget(vm_ext_entry)

        layout_left.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_middle.addWidget(layout_left_widget)

        # Center (VM Management)

        layout_center_widget = QWidget()
        layout_center_widget.setMinimumWidth(400)
        layout_center_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout_center = QVBoxLayout(layout_center_widget)
        layout_center.addWidget(
            QLabel("Virtual Machine Management", alignment=Qt.AlignmentFlag.AlignCenter)
            )
        layout_middle.addWidget(layout_center_widget)

        # Right (VM Sizes)

        layout_right_widget = QWidget()
        layout_right_widget.setMinimumWidth(200)
        layout_right_widget.setMaximumWidth(500)
        layout_right = QVBoxLayout(layout_right_widget)
        layout_right.addWidget(
            QLabel("Virtual Machine Sizes", alignment=Qt.AlignmentFlag.AlignCenter)
        )
        layout_middle.addWidget(layout_right_widget)

        layout_back.addLayout(layout_middle)

        # Bottom

        message_label = QLabel()
        layout_back.addWidget(message_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout_back.addWidget(QLabel("v" + VERSION, alignment=Qt.AlignmentFlag.AlignRight))

        # Get Virtual Machines

        missing_setting = False
        if (
            self.settings["server_hostname"] == "" or self.settings["server_username"] == "" or
            self.settings["local_vms_path"] == "" or self.settings["server_vms_path"] == "" or
            self.settings["vm_ext"] == ""
        ):
            message_label.setText(f"Couldn't read virtual machines, missing required setting(s).")
            missing_setting = True

        if not missing_setting:

            # Load Virtual Machines Config

            icons_dict = {}
            if os.path.exists(PATH_VMS_CONF):
                with open(PATH_VMS_CONF, "r") as file:
                    for line in file:
                        name, icon = line.split(" / ")
                        icons_dict[name] = icon

            # Get Local VMs

            self.vms = []

            spec = importlib.util.spec_from_file_location("get-machines", PATH_SCRIPTS + "/get-machines.py")
            get_machines = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(get_machines)
            vms_str = get_machines.get_machines(
                self.settings["local_vms_path"], self.settings["vm_ext"]
            )
            for line in vms_str.splitlines():
                size, name = line.split(" ", 1)
                icon = self.get_icon(name, self.settings["local_vms_path"], icons_dict)
                self.vms.append(VirtualMachine(name, local_size=int(size), icon=icon))

            # Connect to Server

            try:
                self.connect_ssh()
            except Exception as e:
                QMessageBox.warning(self, "Error Connecting to SSH", str(e))

            else:

                # Get Server VMs

                stdout = self.ssh_exec_command(
                    f"/usr/bin/python3 {PATH_SERVER_SCRIPTS}/get-machines.py " +
                    f"\"{self.settings["server_vms_path"]}\" \"{self.settings["vm_ext"]}\""
                )

                for line in stdout.splitlines():
                    size, name = line.split(" ", 1)
                    found_vm = False
                    for vm in self.vms:
                        if vm.name == name:
                            vm.server_size = int(size)
                            found_vm = True
                            break
                    if not found_vm:
                        icon = self.get_icon(name, self.settings["server_vms_path"], icons_dict)
                        self.vms.append(VirtualMachine(name, server_size=int(size), icon=icon))

                self.ssh.close()

            # Display Virtual Machines

            for vm in self.vms:

                vm_frame = QFrame()
                layout_back = QVBoxLayout(vm_frame)

                # Name

                layout_back.addWidget(QLabel(vm.name))

                layout_bottom = QHBoxLayout()

                # Local VM

                layout_bottom.addWidget(VirtualMachineWidget(vm, True), alignment=Qt.AlignmentFlag.AlignLeft)

                # Status

                # Server VM

                layout_bottom.addWidget(VirtualMachineWidget(vm, False), alignment=Qt.AlignmentFlag.AlignRight)

                layout_back.addLayout(layout_bottom)

                layout_center.addWidget(vm_frame)

    # Functions

    def raise_ssh_error(self, err):
        error_message = QErrorMessage(self)
        error_message.showMessage(err)
        raise ValueError(err)

    def get_password(self, title):
        input_dialog = QInputDialog()
        input_dialog.setWindowTitle(title)
        input_dialog.setLabelText("Enter Password")
        input_dialog.setInputMode(QInputDialog.TextInput)
        input_dialog.setTextEchoMode(QLineEdit.Password)
        input_dialog.resize(300, 200)
        ok = input_dialog.exec()
        password = input_dialog.textValue()
        if ok:
            return password
        return None

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
                if value in ("True", "False"):
                    value = (value == "True")
                self.settings[setting] = value

        for setting in (
            "ssh_auth_type", "ssh_key_path", "ssh_key_type", "ssh_key_encrypted",
            "save_ssh_password", "save_ssh_key_password",
            "server_hostname", "server_username", "local_vms_path", "server_vms_path", "vm_ext"
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

        # Password Connection

        if self.settings["ssh_auth_type"] == "Password":
            password = None
            if self.settings["save_ssh_password"]:
                password = keyring.get_password("VM Manager", "SSH Password")
            if password is None:
                password = self.get_password("SSH Password")
                if password is None:
                    raise ValueError("Auth type is password and no password found or given.")
            self.ssh.connect(
                self.settings["server_hostname"], username=self.settings["server_username"],
                password=password
            )

        # Key Connection

        else:

            password = None
            if self.settings["ssh_key_encrypted"]:
                if self.settings["save_ssh_key_password"]:
                    password = keyring.get_password("VM Manager", "SSH Key Password")
                if password is None:
                    password = self.get_password("SSH Key Password")
                    if password is None:
                        raise ValueError("Key encrypted and no password found or given.")

            if self.settings["ssh_key_type"] == "RSA":
                key = paramiko.RSAKey.from_private_key_file(self.settings["ssh_key_path"], password)
            elif self.settings["ssh_key_type"] == "ECDSA":
                key = paramiko.ECDSAKey.from_private_key_file(
                    self.settings["ssh_key_path"], password
                )
            else:
                key = paramiko.Ed25519Key.from_private_key_file(
                    self.settings["ssh_key_path"], password
                )
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.settings["server_hostname"], username=self.settings["server_username"],
                pkey=key
            )

        # Install Any Missing Scripts

        if not self.ssh_path_found(PATH_SERVER_SCRIPTS, "d"):
            self.ssh_exec_command("mkdir -p " + PATH_SERVER_SCRIPTS)

        sftp = self.ssh.open_sftp()

        for script in os.listdir(PATH_SCRIPTS):
            local_path = f"{PATH_SCRIPTS}/{script}"
            server_path = f"{PATH_SERVER_SCRIPTS}/{script}".replace("~", "/home/" + self.settings["server_username"], 1)
            if (not os.path.isfile(local_path)) or ((not RELEASE_PATHS) and script.endswith(__file__)):
                continue
            if not self.ssh_path_found(server_path):
                sftp.put(local_path, server_path) # broken

        sftp.close()

    def ssh_path_found(self, path, type = "e"):
        if path[0] == "~":
            path = path.replace("~", "/home/" + self.settings["server_username"], 1)
        return b"found" in self.ssh_exec_command(f"if [ -{type} \"{path}\" ]; then echo found; fi")

    def ssh_exec_command(self, command):
        stdout, stderr = self.ssh.exec_command(command)[1:]
        stderr_data = stderr.read()
        if stderr_data:
            self.raise_ssh_error(f"Error with ssh command \"{command}\": {stderr_data}")
        return stdout.read()

    def get_icon(self, name, vms_path, icons_dict):

        # Check Saved Icons

        icon = icons_dict[name] if name in icons_dict.keys() else None

        if icon is None:

            # Search Function

            def search_icon_names(target):
                nonlocal icon
                for key in ICON_NAMES.keys():
                    found = False
                    for assoc_name in ICON_NAMES[key]:
                        if assoc_name in name.lower():
                            icon = key
                            found = True
                            break
                    if found:
                        break

            # Compare with Name

            search_icon_names(name)

            if icon is None:

                # Look for OS Type

                os_type = None
                for path in os.listdir(vms_path + "/" + name):
                    if path.endswith(".vbox"):
                        with open(f"{vms_path}/{name}/{path}", "r") as file:
                            for line in file.readlines():
                                if line.strip().startswith("<Machine"):
                                    for word in line.strip().split(" "):
                                        if word.startswith("OSType="):
                                            os_type = word[7:].lower()
                                            break
                                    break
                        break

                # Compare with OS Type

                search_icon_names(os_type)

        return icon + ".png"


# Functions

def format_size(size):
    suffixes = {"B", "kiB", "MiB", "GiB", "TiB", "PiB", "EiB"}
    exp = 0
    while (size >= pow(1024, exp + 1)):
        ++exp
    return str(round(size / pow(1024, exp), 1)) + suffixes[exp]


# Main Function

def main():
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()


# Run Main Function

if __name__ == "__main__":
    main()
