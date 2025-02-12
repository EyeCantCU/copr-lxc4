%define incuslibdir %{_prefix}/lib/incus
%bcond_without  check

# https://github.com/lxc/incus
%global goipath github.com/lxc/incus
Version:        0.4

%gometa

%global godocs      AUTHORS
%global golicenses  COPYING

Name:           incus
Release:        0.1%{?dist}
Summary:        Powerful system container and virtual machine manager

# Upstream license specification: Apache-2.0
License:        ASL 2.0
URL:            https://linuxcontainers.org/incus
Source0:        https://linuxcontainers.org/downloads/%{name}/%{name}-%{version}.tar.xz
Source1:        incus.socket
Source2:        incus.service
Source3:        incus-startup.service
Source4:        incus.dnsmasq
Source5:        incus.logrotate
Source6:        shutdown
Source7:        incus.sysctl
Source8:        incus-agent.service
Source9:        incus-agent-setup
Source10:       incus-user.socket
Source11:       incus-user.service
# Latest downloads from https://github.com/swagger-api/swagger-ui/tree/master/dist
Source12:       swagger-ui-bundle.js
Source13:       swagger-ui-standalone-preset.js
Source14:       swagger-ui.css
# Upstream bug fixes merged to master for next release
# Allow offline builds
Patch0:         incus-0.2-doc-Remove-downloads-from-sphinx-build.patch

BuildRequires:  gettext
BuildRequires:  help2man
BuildRequires:  pkgconfig(cowsql)
BuildRequires:  pkgconfig(libacl)
BuildRequires:  pkgconfig(libcap)
BuildRequires:  pkgconfig(libseccomp)
BuildRequires:  pkgconfig(libudev)
BuildRequires:  pkgconfig(lxc)
BuildRequires:  pkgconfig(raft)
BuildRequires:  pkgconfig(sqlite3)

Requires: acl
Requires: attr
Requires: dnsmasq
Requires: (nftables or (ebtables-legacy and iptables-legacy))
Requires: incus-client = %{version}-%{release}
Requires: lxcfs
Requires: rsync
Requires: shadow-utils
Requires: squashfs-tools
Requires: tar
Requires: xdelta
Requires: xz
%{?systemd_requires}
Requires(pre): container-selinux
Requires(pre): shadow-utils

%if %{with check}
BuildRequires:  btrfs-progs
BuildRequires:  dnsmasq
BuildRequires:  ebtables-legacy
BuildRequires:  iptables-legacy
%endif

Suggests: logrotate
# Virtual machine support requires additional packages
Suggests: edk2-ovmf
Suggests: genisoimage
Suggests: qemu-char-spice
Suggests: qemu-device-display-virtio-vga
Suggests: qemu-device-display-virtio-gpu
Suggests: qemu-device-usb-redirect
Suggests: qemu-img
Suggests: qemu-system-x86-core

%description
Container hypervisor based on LXC
Incus offers a REST API to remotely manage containers over the network,
using an image based work-flow and with support for live migration.

This package contains the Incus daemon.

%godevelpkg

%package client
Summary:        Container hypervisor based on LXC - Client

Requires:       gettext

%description client
Incus offers a REST API to remotely manage containers over the network,
using an image based work-flow and with support for live migration.

This package contains the command line client.

%package tools
Summary:        Container hypervisor based on LXC - Extra Tools

Suggests:       rsync
#Suggests:       netcat

%description tools
Incus offers a REST API to remotely manage containers over the network,
using an image based work-flow and with support for live migration.

This package contains extra tools provided with Incus.
 - fuidshift - A tool to map/unmap filesystem uids/gids
 - lxc-to-incus - A tool to migrate LXC containers to Incus
 - lxd-to-incus - A tool to migrate an existing LXD environment to Incus
 - incus-benchmark - A Incus benchmark utility
 - incus-migrate - A physical to container migration tool

%package agent
Summary:        Incus guest agent

%description agent
This packages provides an agent to run inside Incus virtual machine guests.

It has to be installed on the Incus host if you want to allow agent
injection capability when creating a virtual machine.

%package user                                                                                                                                                                                                                                                                                                                 
Summary:        Incus user daemon

%description user
This packages provides an Incus daemon proxy to allow lower privileged users
to automatically have their isolated Incus project.

%package doc
Summary:        Container hypervisor based on LXC - Documentation
BuildArch:      noarch

BuildRequires:  python3-furo
BuildRequires:  python3-linkify-it-py
BuildRequires:  python3-lxd-sphinx-extensions
BuildRequires:  python3-myst-parser
BuildRequires:  python3-sphinx
BuildRequires:  python3-sphinx-copybutton
BuildRequires:  python3-sphinx-design
BuildRequires:  python3-sphinx-notfound-page
BuildRequires:  python3-sphinx-remove-toctrees
BuildRequires:  python3-sphinx-reredirects
BuildRequires:  python3-sphinx-tabs
BuildRequires:  python3-sphinxcontrib-applehelp
BuildRequires:  python3-sphinxcontrib-devhelp
BuildRequires:  python3-sphinxcontrib-htmlhelp
BuildRequires:  python3-sphinxcontrib-jquery
BuildRequires:  python3-sphinxcontrib-jsmath
BuildRequires:  python3-sphinxcontrib-qthelp
BuildRequires:  python3-sphinxcontrib-serializinghtml
BuildRequires:  python3-sphinxext-opengraph

%description doc
Incus offers a REST API to remotely manage containers over the network,
using an image based work-flow and with support for live migration.

This package contains user documentation.

%prep
%goprep -k
%patch0 -p1

%build
export CGO_LDFLAGS_ALLOW="(-Wl,-wrap,pthread_create)|(-Wl,-z,now)"
for cmd in incusd incus-user; do
    BUILDTAGS="libsqlite3" %gobuild -o %{gobuilddir}/lib/$cmd %{goipath}/cmd/$cmd
done
for cmd in incus fuidshift incus-benchmark lxc-to-incus; do
    BUILDTAGS="libsqlite3" %gobuild -o %{gobuilddir}/bin/$cmd %{goipath}/cmd/$cmd
done

export CGO_ENABLED=0
BUILDTAGS="netgo" %gobuild -o %{gobuilddir}/bin/incus-migrate %{goipath}/cmd/incus-migrate
BUILDTAGS="agent netgo" %gobuild -o %{gobuilddir}/bin/incus-agent %{goipath}/cmd/incus-agent
unset CGO_ENABLED

pushd cmd/lxd-to-incus
ln -s vendor src
GOPATH=${GOPATH}$(pwd) %gobuild -o %{gobuilddir}/bin/lxd-to-incus ./
popd

# build documentation
mkdir -p doc/.sphinx/_static/swagger-ui
cp %{SOURCE12} %{SOURCE13} %{SOURCE14} doc/.sphinx/_static/swagger-ui
sed -i 's|^path.*$|path = "%{gobuilddir}"|' doc/conf.py
sphinx-build -c doc/ -b dirhtml doc/ doc/html/
rm -rf doc/html/{.buildinfo,.doctrees}

# build translations
rm -f po/zh_Hans.po po/zh_Hant.po    # remove invalid locales
make %{?_smp_mflags} build-mo

# generate man-pages
mkdir %{gobuilddir}/man
%{gobuilddir}/bin/incus manpage %{gobuilddir}/man/
%{gobuilddir}/lib/incusd manpage %{gobuilddir}/man/
help2man %{gobuilddir}/bin/fuidshift -n "uid/gid shifter" --no-info --no-discard-stderr > %{gobuilddir}/man/fuidshift.1
help2man %{gobuilddir}/bin/incus-benchmark -n "The container lightervisor - benchmark" --no-info --no-discard-stderr > %{gobuilddir}/man/incus-benchmark.1
help2man %{gobuilddir}/bin/incus-migrate -n "Physical to container migration tool" --no-info --no-discard-stderr > %{gobuilddir}/man/incus-migrate.1
help2man %{gobuilddir}/bin/lxc-to-incus -n "Convert LXC containers to Incus" --no-info --no-discard-stderr > %{gobuilddir}/man/lxc-to-incus.1
help2man %{gobuilddir}/bin/lxd-to-incus -n "LXD to Incus migration tool" --no-info --no-discard-stderr > %{gobuilddir}/man/lxd-to-incus.1
help2man %{gobuilddir}/bin/incus-agent -n "Incus virtual machine guest agent" --no-info --no-discard-stderr > %{gobuilddir}/man/incus-agent.1

%install
%gopkginstall

# install binaries
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

# extra configs
install -Dpm 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/dnsmasq.d/incus
install -Dpm 0644 %{SOURCE5} %{buildroot}%{_sysconfdir}/logrotate.d/incus
install -Dpm 0644 %{SOURCE7} %{buildroot}%{_sysconfdir}/sysctl.d/10-incus-inotify.conf

# install bash completion
install -Dpm 0644 scripts/bash/incus %{buildroot}%{_datadir}/bash-completion/completions/incus

# install systemd units
install -d -m 0755 %{buildroot}%{_unitdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/
install -p -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/
install -p -m 0644 %{SOURCE3} %{buildroot}%{_unitdir}/
install -p -m 0644 %{SOURCE8} %{buildroot}%{_unitdir}/
install -p -m 0644 %{SOURCE10} %{buildroot}%{_unitdir}/
install -p -m 0644 %{SOURCE11} %{buildroot}%{_unitdir}/
install -d -m 0755 %{buildroot}/lib/systemd
install -p -m 0755 %{SOURCE9} %{buildroot}/lib/systemd/

# install lib
install -d -m 0755 %{buildroot}%{incuslibdir}
install -m 0755 -vp %{gobuilddir}/lib/* %{buildroot}%{incuslibdir}/
install -m 0755 -p %{SOURCE6} %{buildroot}%{incuslibdir}/

# install manpages
install -d %{buildroot}%{_mandir}/man1
cp -p %{gobuilddir}/man/*.1 %{buildroot}%{_mandir}/man1/

# cache and log directories
install -d -m 0711 %{buildroot}%{_localstatedir}/lib/%{name}
install -d -m 0755 %{buildroot}%{_localstatedir}/log/%{name}

# language files
install -dm 0755 %{buildroot}%{_datadir}/locale
for mofile in po/*.mo ; do
install -Dpm 0644 ${mofile} %{buildroot}%{_datadir}/locale/$(basename ${mofile%%.mo})/LC_MESSAGES/%{name}.mo
done
%find_lang incus

%if %{with check}
%check
export GOPATH=%{buildroot}/%{gopath}:%{gopath}
export CGO_LDFLAGS_ALLOW="(-Wl,-wrap,pthread_create)|(-Wl,-z,now)"

# Add libsqlite3 tag to go test
%define gotestflags -buildmode pie -compiler gc -v -tags libsqlite3

%gocheck -v -t %{goipath}/test \
    -d %{goipath}/cmd/lxc-to-incus  # lxc-to-incus test fails, see ganto/copr-lxc4#23

%endif

%pre
# check for existence of incus-admin group, create it if not found
getent group %{name} > /dev/null || groupadd -r %{name}
getent group %{name}-admin > /dev/null || groupadd -r %{name}-admin

%post
%systemd_post %{name}.socket
%systemd_post %{name}.service
%systemd_post %{name}-startup.service
%systemd_post %{name}-user.socket
%systemd_post %{name}-user.service

%post agent
%systemd_post %{name}-agent.service

%preun
%systemd_preun %{name}.socket
%systemd_preun %{name}.service
%systemd_preun %{name}-startup.service
%systemd_preun %{name}-user.socket
%systemd_preun %{name}-user.service

%preun agent
%systemd_preun %{name}-agent.service

%files
%license %{golicenses}
%config(noreplace) %{_sysconfdir}/dnsmasq.d/incus
%config(noreplace) %{_sysconfdir}/logrotate.d/incus
%config(noreplace) %{_sysconfdir}/sysctl.d/10-incus-inotify.conf
%{_unitdir}/%{name}.socket
%{_unitdir}/%{name}.service
%{_unitdir}/%{name}-startup.service
%{_unitdir}/%{name}-user.socket
%{_unitdir}/%{name}-user.service
%dir %{incuslibdir}
%{incuslibdir}/*
%{_mandir}/man1/incusd*.1.*
%dir %{_localstatedir}/log/%{name}
%defattr(-, root, root, 0711)
%dir %{_localstatedir}/lib/%{name}

%gopkgfiles

%files client -f incus.lang
%license %{golicenses}
%{_bindir}/%{name}
%{_datadir}/bash-completion/completions/%{name}
%{_mandir}/man1/%{name}*.1.*
%exclude %{_mandir}/man1/incusd*.1.*
%exclude %{_mandir}/man1/incus-agent.1.*
%exclude %{_mandir}/man1/incus-benchmark.1.*
%exclude %{_mandir}/man1/incus-migrate.1.*
%exclude %{_mandir}/man1/lxc-to-incus.1.*
%exclude %{_mandir}/man1/lxd-to-incus.1.*

%files tools
%license %{golicenses}
%{_bindir}/fuidshift
%{_bindir}/incus-benchmark
%{_bindir}/incus-migrate
%{_bindir}/lxc-to-incus
%{_bindir}/lxd-to-incus
%{_mandir}/man1/fuidshift.1.*
%{_mandir}/man1/incus-benchmark.1.*
%{_mandir}/man1/incus-migrate.1.*
%{_mandir}/man1/lxc-to-incus.1.*
%{_mandir}/man1/lxd-to-incus.1.*

%files agent
%license %{golicenses}
%{_bindir}/incus-agent
%{_unitdir}/%{name}-agent.service
/lib/systemd/%{name}-agent-setup
%{_mandir}/man1/incus-agent.1.*

%files doc
%license %{golicenses}
%doc doc/html

%changelog
* Thu Dec 21 2023 Reto Gantenbein <reto.gantenbein@linuxmonk.ch> 0.4-0.1
- Update to 0.4
- Update swagger-ui to v5.10.5

* Fri Nov 10 2023 Reto Gantenbein <reto.gantenbein@linuxmonk.ch> 0.2-0.2
- Fix envvar for OVMF and documentation

* Mon Oct 30 2023 Reto Gantenbein <reto.gantenbein@linuxmonk.ch> 0.2-0.1
- Update to 0.2
- Update swagger-ui to v5.9.1

* Sun Oct 15 2023 Reto Gantenbein <reto.gantenbein@linuxmonk.ch> 0.1-0.2
- Fix libdir path

* Sun Oct 15 2023 Reto Gantenbein <reto.gantenbein@linuxmonk.ch> 0.1-0.1
- Initial package

