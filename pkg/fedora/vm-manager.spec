Name: vm-manager
Version: VERSION
Release: %{?dist}
Packager: Liam Ralph <liamralph@tutamail.com>
Summary: Scripts for managing versions of virtual machines.

License: MIT
URL: https://github.com/liam-ralph/vm-manager
Requires: python3 >= 3.10, python3-pyside6 >= 6.4, python3-paramiko, python3-keyring
Source0: %{name}-%{version}.tar.gz

%description
Scripts for managing versions of virtual machines.

%global debug_package %{nil}

%prep
%autosetup

%install
install -Dm755 usr/bin/vm-manager.py "$RPM_BUILD_ROOT/usr/bin/vm-manager.py"
install -Dm644 usr/share/applications/vm-manager.desktop \
    "$RPM_BUILD_ROOT/usr/share/applications/vm-manager.desktop"
install -Dm644 usr/share/doc/vm-manager/copyright \
    "$RPM_BUILD_ROOT/usr/share/doc/vm-manager/copyright"
install -Dm644 usr/share/doc/vm-manager/README.md \
    "$RPM_BUILD_ROOT/usr/share/doc/vm-manager/README.md"
install -Dm644 usr/share/doc/vm-manager/CHANGELOG.md \
    "$RPM_BUILD_ROOT/usr/share/doc/vm-manager/CHANGELOG.md"
install -Dm644 usr/share/icons/hicolor/512x512/apps/vm-manager.png \
    "$RPM_BUILD_ROOT/usr/share/icons/hicolor/512x512/apps/vm-manager.png"
install -Dm644 usr/share/licenses/vm-manager/LICENSE \
    "$RPM_BUILD_ROOT/usr/share/licenses/vm-manager/LICENSE"
install -Dm644 usr/share/vm-manager/defaults.conf \
    "$RPM_BUILD_ROOT/usr/share/vm-manager/defaults.conf"
find usr/share/vm-manager/icons -type f \
    -exec install -Dm644 {} "$RPM_BUILD_ROOT/{}" \;

%clean
rm -rf $RPM_BUILD_ROOT

%postun
if [[ -n $XDG_CONFIG_DIR && ! -z $XDG_CONFIG_DIR ]]; then
    rm -rf "$XDG_CONFIG_DIR/vm-manager"
else
    rm -rf /home/*/.config/vm-manager
fi

%files
/usr/bin/vm-manager.py
/usr/share/applications/vm-manager.desktop
/usr/share/doc/vm-manager/copyright
/usr/share/doc/vm-manager/README.md
/usr/share/doc/vm-manager/CHANGELOG.md
/usr/share/icons/hicolor/512x512/apps/vm-manager.png
/usr/share/licenses/vm-manager/LICENSE
/usr/share/vm-manager/defaults.conf
/usr/share/vm-manager/icons/

%changelog
%autochangelog
