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
    PATH_ICONS = "/usr/share/vm-manager/icons"
else:
    # Assuming relative to project root, not /src
    PATH_LOGO = os.path.abspath("logo.png")
    PATH_DOC = os.path.abspath("")
    PATH_SETTINGS = os.path.abspath("conf/defaults.conf")
    PATH_ICONS = os.path.abspath("icons")

with open(PATH_DOC + "/README.md", "r") as file:
    for i in range(2):
        file.readline()
    VERSION = file.readline()[12:]


# Classes

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

        settings = load_settings()

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

        layout_left.addWidget(QLabel("SSH Key Path"))
        ssh_key_path_entry = QLineEdit()
        ssh_key_path_entry.setPlaceholderText(settings["ssh_key_path"])
        layout_left.addWidget(ssh_key_path_entry)

        ssh_key_type_combo = QComboBox()
        ssh_key_types = ("RSA", "ECDSA", "Ed25519")
        ssh_key_type_combo.addItems(ssh_key_types)
        ssh_key_type_combo.setCurrentIndex(ssh_key_types.index(settings["ssh_key_type"]))
        layout_left.addWidget(ssh_key_type_combo)

        save_ssh_password_check = QCheckBox("Save SSH Password")
        save_ssh_password_check.setChecked(settings["save_ssh_password"] == "True")
        layout_left.addWidget(save_ssh_password_check)

        save_ssh_key_password_check = QCheckBox("Save SSH Key Password")
        save_ssh_key_password_check.setChecked(settings["save_ssh_key_password"] == "True")
        layout_left.addWidget(save_ssh_key_password_check)

        # Server Address Settings

        layout_left.addSpacing(20)
        layout_left.addWidget(QLabel("Server Address"))

        layout_left.addWidget(QLabel("Server Hostname"))
        server_hostname_entry = QLineEdit()
        server_hostname_entry.setPlaceholderText(settings["server_hostname"])
        layout_left.addWidget(server_hostname_entry)

        layout_left.addWidget(QLabel("Server Username"))
        server_username_entry = QLineEdit()
        server_username_entry.setPlaceholderText(settings["server_username"])
        layout_left.addWidget(server_username_entry)

        # Virtual Machines Path Settings

        layout_left.addSpacing(20)
        layout_left.addWidget(QLabel("Virtual Machines Path"))

        local_vms_path_entry = QLineEdit()
        local_vms_path_entry.setPlaceholderText(settings["local_vms_path"])
        layout_left.addWidget(local_vms_path_entry)

        server_vms_path_entry = QLineEdit()
        server_vms_path_entry.setPlaceholderText(settings["server_vms_path"])
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

        required_settings = (
            "server_hostname", "server_username", "local_vms_path", "server_vms_path"
        )
        missing_setting = False
        for required_setting in required_settings:
            if settings[required_setting] == "":
                message_label.setText(f"Couldn't read machines: {required_setting} not set.")
                missing_setting = True
                break

        if not missing_setting:
            pass

    # Functions

    def show_info(self):
        info_window = InfoWindow()
        info_window.show()


# Functions

def load_settings(depth = 0):
    """
    Load user settings from **PATH_SETTINGS**.

    :return: A dictionary of settings of form {setting, value}, both str.
    """

    settings = {}

    try:
        with open(PATH_SETTINGS, "r") as file:
            for line in file:
                if (line.startswith("#") or line == "\n"):
                    continue
                line = line.strip()
                if line.endswith("="):
                    settings[line[:-1]] = ""
                    continue
                setting, value = line.split("=")
                settings[setting] = value

    except FileNotFoundError as error:
        if depth == 0:
            if not os.path.exists(PATH_SETTINGS) and RELEASE_PATHS:
                shutil.copy("/usr/share/vm-manager/defaults.conf", PATH_SETTINGS)
                return load_settings(1)
            else:
                raise error
        else:
            raise error

    return settings


def set_setting(setting, value, depth = 0):
    """
    Set user setting in **PATH_SETTINGS**.

    :param setting: The setting to set.
    :param value: The value to set **setting** to.
    """

    try:
        with open(PATH_SETTINGS, "r+") as file:
            pass

    except FileNotFoundError as error:
        if depth == 0:
            if not os.path.exists(PATH_SETTINGS) and RELEASE_PATHS:
                shutil.copy("/usr/share/vm-manager/defaults.conf", PATH_SETTINGS)
                return set_setting(setting, value, 1)
            else:
                raise error
        else:
            raise error


# Main Function

def main():
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()


# Run Main Function

if __name__ == "__main__":
    main()
