Summary:	Free version of the SSH connectivity tools
Name:		openssh
Version:	7.1p2
Release:	4%{?dist}
License:	BSD
URL:		http://openssh.org
Group:		System Environment/Security
Vendor:		VMware, Inc.
Distribution: Photon
Source0:	http://ftp.openbsd.org/pub/OpenBSD/OpenSSH/portable/%{name}-%{version}.tar.gz
%define sha1 openssh=9202f5a2a50c8a55ecfb830609df1e1fde97f758
Source1:	http://www.linuxfromscratch.org/blfs/downloads/systemd/blfs-systemd-units-20140907.tar.bz2
%define sha1 blfs-systemd-units=713afb3bbe681314650146e5ec412ef77aa1fe33
Patch1:		blfs_systemd_fixes.patch
Patch2:         openssh-7.1p2-skip-long-passwords.patch
BuildRequires:  openssl-devel
BuildRequires:	Linux-PAM
BuildRequires:  krb5
BuildRequires:  e2fsprogs-devel
BuildRequires:  systemd
Requires:       systemd
Requires:	openssl
Requires:	Linux-PAM
Requires: 	shadow
%description
The OpenSSH package contains ssh clients and the sshd daemon. This is
useful for encrypting authentication and subsequent traffic over a 
network. The ssh and scp commands are secure implementions of telnet 
and rcp respectively.
%prep
%setup -q
tar xf %{SOURCE1}
%patch1 -p0
%patch2 -p1
%build
./configure \
	CFLAGS="%{optflags}" \
	CXXFLAGS="%{optflags}" \
	--prefix=%{_prefix} \
	--bindir=%{_bindir} \
	--libdir=%{_libdir} \
	--sysconfdir=/etc/ssh \
	--datadir=/usr/share/sshd \
	--with-md5-passwords \
	--with-privsep-path=/var/lib/sshd \
    	--with-pam \
	--with-maintype=man \
	--with-kerberos5=/usr
make
%install
[ %{buildroot} != "/"] && rm -rf %{buildroot}/*
make DESTDIR=%{buildroot} install
install -vdm755 %{buildroot}/var/lib/sshd
echo "PermitRootLogin no" >> %{buildroot}/etc/ssh/sshd_config
echo "UsePAM yes" >> %{buildroot}/etc/ssh/sshd_config
#	Install daemon script
pushd blfs-systemd-units-20140907
make DESTDIR=%{buildroot} install-sshd
popd

cat << EOF > %{buildroot}/lib/systemd/system/sshd.service
[Unit]
Description=OpenSSH Daemon
After=network.target sshd-keygen.service

[Service]
ExecStart=/usr/sbin/sshd -D
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat << EOF >> %{buildroot}/lib/systemd/system/sshd-keygen.service
[Unit]
Description=Generate sshd host keys
ConditionPathExists=|!/etc/ssh/ssh_host_rsa_key
ConditionPathExists=|!/etc/ssh/ssh_host_ecdsa_key
ConditionPathExists=|!/etc/ssh/ssh_host_ed25519_key
Before=sshd.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/ssh-keygen -A
[Install]
WantedBy=multi-user.target
EOF

%{_fixperms} %{buildroot}/*
%check
make -k check |& tee %{_specdir}/%{name}-check-log || %{nocheck}

%pre
getent group sshd >/dev/null || groupadd -g 50 sshd
getent passwd sshd >/dev/null || useradd -c 'sshd PrivSep' -d /var/lib/sshd -g sshd -s /bin/false -u 50 sshd

%preun
%systemd_preun sshd.service sshd-keygen.service

%post
/sbin/ldconfig
if [ $1 -eq 1 ] ; then
    chown -v root:sys /var/lib/sshd
fi
%systemd_post sshd.service sshd-keygen.service

%postun
/sbin/ldconfig
%systemd_postun_with_restart sshd.service sshd-keygen.service
if [ $1 -eq 0 ] ; then
    if getent passwd sshd >/dev/null; then
        userdel sshd
    fi
    if getent group sshd >/dev/null; then
        groupdel sshd
    fi
fi

%clean
rm -rf %{buildroot}/*
%files
%defattr(-,root,root)
%attr(0755,root,root) %dir %{_sysconfdir}/ssh
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/ssh/moduli
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/ssh/ssh_config
%attr(0600,root,root) %config(noreplace) %{_sysconfdir}/ssh/sshd_config
/lib/systemd/system/sshd.service
/lib/systemd/system/sshd.socket
/lib/systemd/system/sshd@.service
/lib/systemd/system/sshd-keygen.service
%{_bindir}/*
%{_sbindir}/*
%{_libexecdir}/*
%{_mandir}/man1/*
%{_mandir}/man5/*
%{_mandir}/man8/*
%attr(700,root,sys)/var/lib/sshd
%changelog
*	Thu Sep 15 2016 Anish Swaminathan <anishs@vmware.com> 7.1p2-4
-	Add patch to fix CVE-2016-6515
*	Tue May 24 2016 Priyesh Padmavilasom <ppadmavilasom@vmware.com> 7.1p2-3
-	GA - Bump release of all rpms
*	Wed May 04 2016 Anish Swaminathan <anishs@vmware.com> 7.1p2-2
-	Edit scriptlets.
*   	Thu Mar 17 2016 Xiaolin Li <xiaolinl@vmware.com> 7.1p2-1
-   	Updated to version 7.1p2
*	Fri Feb 05 2016 Anish Swaminathan <anishs@vmware.com> 6.6p1-6
-	Add pre install scripts in the rpm
*   	Tue Jan 12 2016 Anish Swaminathan <anishs@vmware.com>  6.6p1-5
-   	Change config file attributes.
*   	Thu Dec 10 2015 Xiaolin Li <xiaolinl@vmware.com> 6.6p1-4
-   	Add systemd to Requires and BuildRequires.
-   	Use systemctl to enable/disable service.
*	Fri Jul 17 2015 Divya Thaluru <dthaluru@vmware.com> 6.6p1-3
-	Enabling ssh-keygen service by default and fixed service file to execute only once.
*	Tue May 19 2015 Sharath George <sharathg@vmware.com> 6.6p1-2
-	Bulding ssh server with kerberos 5.
*	Wed Nov 5 2014 Divya Thaluru <dthaluru@vmware.com> 6.6p1-1
-	Initial build.	First version
