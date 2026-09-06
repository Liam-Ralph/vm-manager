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
import subprocess

# Third Party

import keyring
import paramiko

# PySide6

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget
)


# Global Variables

RELEASE_PATHS = False
if RELEASE_PATHS:
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home != None:
        SETTINGS_PATH = os.path.expanduser(xdg_config_home + "/vm-manager.conf")
    else:
        SETTINGS_PATH = os.path.expanduser("~/.config/vm-manager.conf")
else:
    SETTINGS_PATH = os.path.abspath("conf/defaults.conf")
    # Assuming program is run from project root, not /src


# Classes

# MainWindow

class MainWindow(QMainWindow):

    # Constructor

    def __init__(self):

        super().__init__()

        # Setup MainWindow

        self.setWindowTitle("VM Manager")
        # self.setWindowIcon()
        self.showMaximized()
        self.setMinimumSize(600, 400)

        # Create Window

        window = QWidget()
        layout_back = QVBoxLayout(window)
        self.setCentralWidget(window)

        # Left (Settings)

        if not os.path.exists(SETTINGS_PATH):
            shutil.copy("/usr/share/vm-manager/defaults.conf", SETTINGS_PATH)
        settings = self.load_settings()

        # Middle

        # Right (VM Sizes)

    # Functions

    def load_settings(self):
        """
        Load user settings from SETTINGS_PATH.

        :return: A dictionary of settings of form {setting, value}, both str.
        """
        settings = {}
        with open(SETTINGS_PATH, "r") as file:
            for line in file:
                if (line.startswith("#") or line == "\n"):
                    continue
                line = line.strip()
                if line.endswith("="):
                    settings[line[:-1]] = ""
                    continue
                setting, value = line.split("=")
                settings[setting] = value
        return settings


# Main Function

def main():
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()


# Run Main Function

if __name__ == "__main__":
    main()
