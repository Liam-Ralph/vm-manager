# Copyright (C) 2026 Liam Ralph
# https://github.com/liam-ralph

# This program, including this file, is licensed under the MIT/Expat license.
# See LICENSE or this project's source for more information.
# Project source: https://github.com/liam-ralph/vm-manager

# VM Manager, scripts for managing versions of virtual machines.


# Imports

# Standard Library

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
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget
)
from PySide6.QtCore import Qt


# Global Variables

RELEASE_PATHS = False

if RELEASE_PATHS:
    PATH_LOGO = "/usr/share/icons/hicolor/512x512/apps/vm-manager.png"
    PATH_DOC = "/usr/share/doc/vm-manager"
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home != None:
        PATH_SETTINGS = os.path.expanduser(xdg_config_home + "/vm-manager.conf")
    else:
        PATH_SETTINGS = os.path.expanduser("~/.config/vm-manager.conf")
    PATH_DEFAULT_SETTINGS = "/usr/share/vm-manager/defaults.conf"
    PATH_ICONS = "/usr/share/vm-manager/icons"
else:
    # Assuming relative to project root, not /src
    PATH_LOGO = os.path.abspath("logo.png")
    PATH_DOC = os.path.abspath("")
    PATH_SETTINGS = os.path.abspath("conf/vm-manager.conf")
    PATH_DEFAULT_SETTINGS = os.path.abspath("conf/defaults.conf")
    PATH_ICONS = os.path.abspath("icons")

with open(PATH_DOC + "/README.md", "r") as file:
    for i in range(2):
        file.readline()
    VERSION = file.readline()[12:]

SSH_AUTH_TYPES = ("Password", "Key")
SSH_KEY_TYPES = ("RSA", "ECDSA", "Ed25519")


# Classes

# # Settings

# class Settings: # Change this back to a dict

#     def __init__(
#         self, ssh_auth_type, ssh_key_path, ssh_key_type,
#         save_ssh_password_str, save_ssh_key_password_str,
#         server_hostname, server_username, local_vms_path, server_vms_path
#     ):
#         self.ssh_auth_type = ssh_auth_type
#         self.ssh_key_path = ssh_key_path
#         self.ssh_key_type = ssh_key_type
#         self.save_ssh_password = (save_ssh_password_str == "True")
#         self.save_ssh_key_password = (save_ssh_key_password_str == "True")
#         self.server_hostname = server_hostname
#         self.server_username = server_username
#         self.local_vms_path = local_vms_path
#         self.server_vms_path = server_vms_path

# Virtual Machine

class VirtualMachine:

    def __init__(self, name, icon, size):
        self.name = name
        self.icon = icon
        self.size = size

# Info Window

class InfoWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        # Setup Info Window

        self.setWindowTitle("VM Manager Info")

        # Create Window

        window = QWidget()
        layout_back = QVBoxLayout(window)
        self.setCentralWidget(window)

# Main Window

class MainWindow(QMainWindow):

    # Constructor

    def __init__(self):

        super().__init__()

        # Setup Main Window

        self.setWindowTitle("VM Manager")
        # self.setWindowIcon()
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

        save_ssh_password_check = QCheckBox("Save SSH Password")
        save_ssh_password_check.setChecked(self.settings["save_ssh_password"])
        layout_left.addWidget(save_ssh_password_check)

        if self.settings["save_ssh_password"]:
            save_ssh_password_button = QPushButton("Set Saved SSH Password")
            def save_ssh_password():
                password, ok = QInputDialog.getText(self, "SSH Password", "Enter Password")
                if ok:
                    keyring.set_password("VM Manager", "SSH Password", password)
            save_ssh_password_button.clicked.connect(save_ssh_password)
            layout_left.addWidget(save_ssh_password_button)

        clear_ssh_password_button = QPushButton("Clear Saved SSH Password")
        clear_ssh_password_button.clicked.connect(lambda: keyring.delete_password("VM Manager", "SSH Password"))
        layout_left.addWidget(clear_ssh_password_button)

        save_ssh_key_password_check = QCheckBox("Save SSH Key Password")
        save_ssh_key_password_check.setChecked(self.settings["save_ssh_key_password"])
        layout_left.addWidget(save_ssh_key_password_check)

        if self.settings["save_ssh_key_password"]:
            save_ssh_key_password_button = QPushButton("Set Saved SSH Key Password")
            def save_ssh_key_password():
                password, ok = QInputDialog.getText(self, "SSH Key Password", "Enter Password")
                if ok:
                    keyring.set_password("VM Manager", "SSH Key Password", password)
            save_ssh_key_password_button.clicked.connect(save_ssh_key_password)
            layout_left.addWidget(save_ssh_key_password_button)

        clear_ssh_key_password_button = QPushButton("Clear Saved SSH Key Password")
        clear_ssh_key_password_button.clicked.connect(lambda: keyring.delete_password("VM Manager", "SSH Key Password"))
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

        # Virtual Machines Path Settings

        layout_left.addSpacing(20)
        layout_left.addWidget(QLabel("Virtual Machines Path"))

        local_vms_path_entry = QLineEdit()
        local_vms_path_entry.setPlaceholderText(self.settings["local_vms_path"])
        layout_left.addWidget(local_vms_path_entry)

        server_vms_path_entry = QLineEdit()
        server_vms_path_entry.setPlaceholderText(self.settings["server_vms_path"])
        layout_left.addWidget(server_vms_path_entry)

        layout_left.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_middle.addWidget(layout_left_widget)

        # Center (VM Management)

        layout_center_widget = QWidget()
        layout_center_widget.setMinimumWidth(400)
        layout_center_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout_center = QVBoxLayout(layout_center_widget)
        layout_center.addWidget(
            QLabel("Virtual Machine Sizes", alignment=Qt.AlignmentFlag.AlignCenter)
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

        # Get Machines

        missing_setting = False
        if (
            self.settings["server_hostname"] == "" or self.settings["server_username"] == "" or
            self.settings["local_vms_path"] == "" or self.settings["server_vms_path"] == ""
        ):
            message_label.setText(f"Couldn't read machines.")
            missing_setting = True

        if not missing_setting:

            # Connect to Server

            ssh = paramiko.SSHClient()
            if (self.settings["ssh_auth_type"] == "Password"):
                found_password = False
                if (self.settings["save_ssh_password"]):
                    password = keyring.get_password("VM Manager", "SSH Password")
                    if password is not None:
                        found_password = True
                if not found_password:
                    ok = False
                    while not ok:
                        password, ok = QInputDialog.getText(self, "SSH Password", "Enter Password")
                ssh.connect(self.settings["server_hostname"], self.settings["server_username"], password)

    # Functions

    def load_settings(self, depth = 0):
        """
        Load user settings from **PATH_SETTINGS**.

        :return: An instance of the **Settings** class containing the loaded settings.
        """

        self.settings = {}

        try:
            with open(PATH_SETTINGS, "r") as file:
                for line in file:
                    if (line[0] in ("#", "\n")):
                        continue
                    line = line.strip()
                    if line.endswith("="):
                        self.settings[line[:-1]] = ""
                        continue
                    setting, value = line.split("=")
                    if value in ("True", "False"):
                        value = (value == "True")
                    self.settings[setting] = value

        except FileNotFoundError as e:
            if depth == 0:
                if not os.path.exists(PATH_SETTINGS):
                    shutil.copy(PATH_DEFAULT_SETTINGS, PATH_SETTINGS)
                    return self.load_settings(1)
                else:
                    raise e
            else:
                raise e

        for setting in (
            "ssh_auth_type", "ssh_key_path", "ssh_key_type",
            "save_ssh_password", "save_ssh_key_password",
            "server_hostname", "server_username", "local_vms_path", "server_vms_path"
        ):
            if setting not in self.settings.keys():
                raise ValueError("Missing setting: " + setting)

    def set_setting(self, setting, value, depth = 0):
        """
        Set user setting in **PATH_SETTINGS**.

        :param setting: The setting to set.
        :param value: The value to set **setting** to.
        """

        try:
            with open(PATH_SETTINGS, "r+") as file:
                pass
            self.settings[setting] = value

        except FileNotFoundError as e:
            if depth == 0:
                if not os.path.exists(PATH_SETTINGS) and RELEASE_PATHS:
                    shutil.copy(PATH_DEFAULT_SETTINGS, PATH_SETTINGS)
                    return self.set_setting(setting, value, 1)
                else:
                    raise e
            else:
                raise e

    def show_info(self):
        """Open the info window."""
        info_window = InfoWindow()
        info_window.show()


# Main Function

def main():
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()


# Run Main Function

if __name__ == "__main__":
    main()
