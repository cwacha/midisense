#!/bin/bash

TMP=`pwd`; cd `dirname $0`; BASEDIR=`pwd`; cd $TMP

all() {
    echo "# building: $app_pkgname"
    clean && import && pkg
}

_init() {
    app_pkgid="midisense"
    app_displayname="midisense"
    app_version=`head -20 $BASEDIR/../src/midisense.py | grep VERSION | sed 's/["=]/ /g' | awk '{print $2}'`
    app_revision=`git rev-list --count HEAD`
    app_build=`git rev-parse --short HEAD`

    app_pkgname="$app_pkgid-$app_version-$app_revision-$app_build"
}

_template() {
    filename="$1"
    template="$2"
    
    [ -z "$template" ] && template="$filename.tpl"
    
    cat $template | sed '
    s/%app_pkgid%/'"${app_pkgid}"'/g
    s/%app_displayname%/'"${app_displayname}"'/g
    s/%app_version%/'"${app_version}"'/g
    s/%app_revision%/'"${app_revision}"'/g
    s/%app_build%/'"${app_build}"'/g
    ' > $filename
}

import() {
    echo "##### importing"
    [ -d BUILD ] && rm -rf BUILD
    mkdir BUILD
    mkdir -p BUILD/usr/bin
    mkdir -p BUILD/etc/udev/rules.d
    mkdir -p BUILD/lib/systemd/system
    
    cp ../src/midisense.py BUILD/usr/bin
    cp ../src/*.rules BUILD/etc/udev/rules.d
    cp ../src/*.service BUILD/lib/systemd/system
    
    mkdir BUILD/DEBIAN
    cp dpkg/* BUILD/DEBIAN
    _template BUILD/DEBIAN/control
    rm BUILD/DEBIAN/control.tpl
}

pkg() {
    echo "##### packaging"
    
    dpkg-deb --build --root-owner-group BUILD && dpkg-name BUILD.deb
}

clean() {
    echo "##### cleaning"
    rm -rf BUILD
    rm -rf *.deb
}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <action>"
    echo
    echo "ACTIONS:"
    declare -F | awk '{print $3}' | grep -v ^_ | awk '{print "    "$1}'
    exit
fi

action="$1"
shift

type "$action" >/dev/null
[ $? -ne 0 ] && echo "no such action: $action" && exit 1

cd $BASEDIR
_init

$action $*
echo "##### done"
