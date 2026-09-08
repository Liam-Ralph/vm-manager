#!/bin/bash

# Get Program Version

while read p; do
    if [[ $p == "### Version "* ]]; then
        version=${p:12}
        break
    fi
done < ../README.md

# Check Argument Number

if (( $# != 1 )); then
    echo -e "Expected 1 argument, received $#."
    exit 1
fi

# Build usr Directory

cd ../

if [[ -e "pkg/usr" ]]; then
    rm -rf pkg/usr
fi
mkdir pkg/usr
install -Dm755 src/vm-manager.py pkg/usr/bin/vm-manager.py
install -Dm644 pkg/resources/vm-manager.desktop pkg/usr/share/applications/vm-manager.desktop
install -Dm644 pkg/resources/copyright pkg/usr/share/doc/vm-manager/copyright
install -Dm644 README.md pkg/usr/share/doc/vm-manager/README.md
install -Dm644 CHANGELOG.md pkg/usr/share/doc/vm-manager/CHANGELOG.md
install -Dm644 logo.png pkg/usr/share/icons/hicolor/512x512/apps/vm-manager.png
install -Dm644 LICENSE pkg/usr/share/licenses/vm-manager/LICENSE
install -Dm644 conf/defaults.conf pkg/usr/share/vm-manager/defaults.conf
install -Dm644 src/server-get-machines.py pkg/usr/share/vm-manager/scripts/server-get-machines.py
find icons -type f -exec install -Dm644 {} pkg/usr/share/vm-manager/{} \;

cd pkg

# Build Package

if [[ $1 == "debian" ]]; then

    # Setup Build Path

    build_path="vm-manager_${version}_x86_64"
    rm -rf $build_path
    mkdir -p $build_path/DEBIAN

    # Copy usr Directory and Debian Files

    cp -a usr $build_path/usr

    cp debian/control $build_path/DEBIAN
    cp debian/postrm $build_path/postrm
    sed -i -e "s/VERSION/$version/g" $build_path/DEBIAN/control
    sed -i -e "s/INSTALLED_SIZE/$(du -s $build_path/usr | awk '{print $1}')/g" \
        $build_path/DEBIAN/control

    # Package

    if [[ -f "${build_path}.deb" ]]; then
        rm -f $build_path.deb
    fi
    dpkg -b $build_path
    rm -rf $build_path

elif [[ $1 == "fedora" ]]; then

    # Setup Build Path

    build_path="rpmbuild"
    rm -rf $build_path
    source_dir=vm-manager-$version
    mkdir -p $build_path/{BUILD,RPMS,SOURCES/${source_dir},SPECS,SRPMS}

    # Copy usr Directory and Spec File

    cp -a usr $build_path/SOURCES/$source_dir/usr
    cd $build_path/SOURCES/
    tar -czf $source_dir.tar.gz $source_dir
    cd ../../

    cp fedora/vm-manager.spec $build_path/SPECS/vm-manager.spec
    sed -i -e "s/VERSION/$version/g" $build_path/SPECS/vm-manager.spec

    # Build and Copy Package

    if [[ -e "~/rpmbuild" ]]; then
        mv ~/rpmbuild ~/rpmbuild-backup
    fi

    mv $build_path ~/rpmbuild/
    cd ~/rpmbuild/
    rpmbuild -bb SPECS/vm-manager.spec
    cd -
    mv ~/rpmbuild/ $build_path
    mv $build_path/RPMS/x86_64/vm-manager-*.rpm ./vm-manager_${version}_x86_64.rpm
    rm -rf $build_path

elif [[ $1 == "arch" ]]; then

    # Setup Build Path

    build_path="package-build"
    rm -rf $build_path
    mkdir -p $build_path/vm-manager-$version

    # Copy usr Directory and PKGBUILD

    cp -a usr $build_path/vm-manager-$version/usr
    cd $build_path
    tar -czf vm-manager-$version.tar.gz vm-manager-$version
    rm -rf vm-manager-$version
    cd ..

    cp arch/PKGBUILD $build_path/PKGBUILD
    sed -i -e "s/VERSION/$version/g" $build_path/PKGBUILD
    sha256sum=$(sha256sum $build_path/vm-manager-$version.tar.gz | awk '{print $1}')
    sed -i -e "s/SHA256SUM/$sha256sum/g" $build_path/PKGBUILD

    # Package

    cd $build_path
    makepkg
    cd ..
    mv $build_path/vm-manager-${version}*.pkg.tar.zst \
        ./vm-manager_${version}_x86_64.pkg.tar.zst
    rm -rf $build_path

else

    # Unknown Distro

    echo -e "Unknown argument, must be \"debian\", \"fedora\", or \"arch\"."
    exit 1

fi
