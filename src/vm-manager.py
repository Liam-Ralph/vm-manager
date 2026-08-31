# Copyright (C) 2026 Liam Ralph
# https://github.com/liam-ralph

# This program, including this file, is licensed under the MIT/Expat license.
# See LICENSE or this project's source for more information.
# Project source: https://github.com/liam-ralph/vm-manager

# VM Manager, scripts for managing versions of virtual machines.


# Imports

# Standard Library

import subprocess

# Third Party

import keyring

# PySide6

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget
)


# MainWindow Class

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        # Setup MainWindow

        self.setWindowTitle("VM Manager")
        # self.setWIndowIcon()
        self.showMaximized()
        self.setMinimumSize(600, 400)

        # Create Window

        window = QWidget()
        layout_back = QVBoxLayout(window)
        self.setCentralWidget(window)


# Main Function

def main():
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()


# Run Main Function

if __name__ == "__main__":
    main()
