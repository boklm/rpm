%define	with_python_subpackage	0%{nil}
%define	with_python_version	2.2%{nil}
%define with_perl_subpackage	0
%define	with_bzip2		1%{nil}
%define	with_apidocs		1%{nil}
%define with_internal_db	1%{nil}
%define strip_binaries		1

# XXX enable at your own risk, CDB access to rpmdb isn't cooked yet.
%define	enable_cdb		create cdb

# XXX legacy requires './' payload prefix to be omitted from rpm packages.
%define	_noPayloadPrefix	1

%define	__prefix	/usr
%{expand: %%define __share %(if [ -d %{__prefix}/share/man ]; then echo /share ; else echo %%{nil} ; fi)}

Summary: The RPM package management system.
Name: rpm
%define version 4.1
Version: %{version}
%{expand: %%define rpm_version %{version}}
Release: 0.07
Group: System Environment/Base
Source: ftp://ftp.rpm.org/pub/rpm/dist/rpm-4.0.x/rpm-%{rpm_version}.tar.gz
Copyright: GPL
Conflicts: patch < 2.5
%ifos linux
Prereq: gawk fileutils textutils mktemp shadow-utils
%endif
Requires: popt = 1.7

%if !%{with_internal_db}
BuildRequires: db3-devel

# XXX glibc-2.1.92 has incompatible locale changes that affect statically
# XXX linked binaries like /bin/rpm.
%ifnarch ia64
Requires: glibc >= 2.1.92
%endif
%endif

BuildRequires: zlib-devel
# XXX Red Hat 5.2 has not bzip2 or python
%if %{with_bzip2}
BuildRequires: bzip2 >= 0.9.0c-2
%endif
%if %{with_python_subpackage}
BuildRequires: python-devel >= %{with_python_version}
%endif
%if %{with_perl_subpackage}
BuildRequires: perl >= 0:5.00503
%endif

BuildRoot: %{_tmppath}/%{name}-root

%description
The RPM Package Manager (RPM) is a powerful command line driven
package management system capable of installing, uninstalling,
verifying, querying, and updating software packages. Each software
package consists of an archive of files along with information about
the package like its version, a description, etc.

%package devel
Summary:  Development files for manipulating RPM packages.
Group: Development/Libraries
Requires: rpm = %{rpm_version}, popt = 1.7

%description devel
This package contains the RPM C library and header files. These
development files will simplify the process of writing programs that
manipulate RPM packages and databases. These files are intended to
simplify the process of creating graphical package managers or any
other tools that need an intimate knowledge of RPM packages in order
to function.

This package should be installed if you want to develop programs that
will manipulate RPM packages and databases.

%package build
Summary: Scripts and executable programs used to build packages.
Group: Development/Tools
Requires: rpm = %{rpm_version}

%description build
The rpm-build package contains the scripts and executable programs
that are used to build packages using the RPM Package Manager.

%if %{with_python_subpackage}
%package python
Summary: Python bindings for apps which will manipulate RPM packages.
Group: Development/Libraries
Requires: rpm = %{rpm_version}
Requires: python >= %{with_python_version}
Requires: popt = 1.7

%description python
The rpm-python package contains a module that permits applications
written in the Python programming language to use the interface
supplied by RPM Package Manager libraries.

This package should be installed if you want to develop Python
programs that will manipulate RPM packages and databases.
%endif

%if %{with_perl_subpackage}
%package perl
Summary: Native bindings to the RPM API for Perl.
Group: Development/Languages
URL: http://www.cpan.org
Provides: perl(RPM::Database) = %{rpm_version}
Provides: perl(RPM::Header) = %{rpm_version}
Requires: rpm = %{rpm_version}
Requires: perl >= 0:5.00503
Requires: popt = 1.7
Obsoletes: perl-Perl-RPM

%description perl
The Perl-RPM module is an attempt to provide Perl-level access to the
complete application programming interface that is a part of the Red
Hat Package Manager (RPM). Rather than have scripts rely on executing
RPM commands and parse the resulting output, this module aims to give
Perl programmers the ability to do anything that would otherwise have
been done in C or C++.

The interface is being designed and laid out as a collection of
classes, at least some of which are also available as tied-hash
implementations.

At this time, the interface only provides access to the database of
installed packages, and header data retrieval for RPM and SRPM files
is not yet installed. Error management and the export of most defined
constants, through RPM::Error and RPM::Constants, respectively, are
also available.

%endif

%package -n popt
Summary: A C library for parsing command line parameters.
Group: Development/Libraries
Version: 1.7

%description -n popt
Popt is a C library for parsing command line parameters. Popt was
heavily influenced by the getopt() and getopt_long() functions, but it
improves on them by allowing more powerful argument expansion. Popt
can parse arbitrary argv[] style arrays and automatically set
variables based on command line arguments. Popt allows command line
arguments to be aliased via configuration files and includes utility
functions for parsing arbitrary strings into argv[] arrays using
shell-like rules.

%prep
%setup -q

%build

%ifos linux
CFLAGS="$RPM_OPT_FLAGS" ./configure --prefix=%{__prefix} --sysconfdir=/etc --localstatedir=/var --infodir='${prefix}%{__share}/info' --mandir='${prefix}%{__share}/man' --with-python=%{with_python_version} --without-javaglue
%else
CFLAGS="$RPM_OPT_FLAGS" ./configure --prefix=%{__prefix}
%endif

# XXX workaround ia64 gcc-3.1-0.18 miscompilation
%ifarch ia64
make CFLAGS="-g -O0 -DIA64_SUCKS_ROCKS" files.o files.lo -C build
%endif

make

%if %{with_perl_subpackage}
{ cd Perl-RPM
  CFLAGS="$RPM_OPT_FLAGS" perl Makefile.PL RPM_BUILD=1
  export SUBDIR="%{_builddir}/%{buildsubdir}"
  make INC="-I. -I$SUBDIR/lib -I$SUBDIR/rpmdb -I$SUBDIR/rpmio -I$SUBDIR/popt" \
    LDDLFLAGS="-shared -L$SUBDIR/lib/.libs -L$SUBDIR/rpmdb/.libs -L$SUBDIR/rpmio/.libs -L$SUBDIR/popt/.libs" %{?_smp_mflags}
}
%endif

%install
rm -rf $RPM_BUILD_ROOT

make DESTDIR="$RPM_BUILD_ROOT" install

%ifos linux

# Save list of packages through cron
mkdir -p ${RPM_BUILD_ROOT}/etc/cron.daily
install -m 755 scripts/rpm.daily ${RPM_BUILD_ROOT}/etc/cron.daily/rpm

mkdir -p ${RPM_BUILD_ROOT}/etc/logrotate.d
install -m 644 scripts/rpm.log ${RPM_BUILD_ROOT}/etc/logrotate.d/rpm

mkdir -p $RPM_BUILD_ROOT/etc/rpm
cat << E_O_F > $RPM_BUILD_ROOT/etc/rpm/macros.db1
%%_dbapi		1
E_O_F
cat << E_O_F > $RPM_BUILD_ROOT/etc/rpm/macros.cdb
%{?enable_cdb:#%%__dbi_cdb	%{enable_cdb}}
E_O_F

mkdir -p $RPM_BUILD_ROOT/var/lib/rpm
for dbi in \
	Basenames Conflictname Dirnames Group Installtid Name Providename \
	Provideversion Removetid Requirename Requireversion Triggername \
	Sigmd5 Sha1header Filemd5s Packages \
	__db.001 __db.002 __db.003 __db.004 __db.005 __db.006 __db.007 \
	__db.008 __db.009
do
    touch $RPM_BUILD_ROOT/var/lib/rpm/$dbi
done

%endif

%if %{with_apidocs}
gzip -9n apidocs/man/man*/* || :
%endif

%if %{with_perl_subpackage}
{ cd Perl-RPM
  eval `perl '-V:installsitearch'`
  eval `perl '-V:installarchlib'`
  mkdir -p $RPM_BUILD_ROOT/$installarchlib
  make PREFIX=${RPM_BUILD_ROOT}%{__prefix} \
    INSTALLMAN1DIR=${RPM_BUILD_ROOT}%{__prefix}%{__share}/man/man1 \
    INSTALLMAN3DIR=${RPM_BUILD_ROOT}%{__prefix}%{__share}/man/man3 \
	install
  rm -f $RPM_BUILD_ROOT/$installarchlib/perllocal.pod
  rm -f $RPM_BUILD_ROOT/$installsitearch/auto/RPM/.packlist
  cd ..
}
%endif

%if %{strip_binaries}
{ cd $RPM_BUILD_ROOT
  %{__strip} ./bin/rpm
  %{__strip} .%{__prefix}/bin/rpm2cpio
}
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%ifos linux
if [ -f /var/lib/rpm/Packages -a -f /var/lib/rpm/packages.rpm ]; then
    echo "
You have both
	/var/lib/rpm/packages.rpm	db1 format installed package headers
	/var/lib/rpm/Packages		db3 format installed package headers
Please remove (or at least rename) one of those files, and re-install.
"
    exit 1
fi
/usr/sbin/groupadd -g 37 rpm				> /dev/null 2>&1
/usr/sbin/useradd  -r -d /var/lib/rpm -u 37 -g 37 rpm	> /dev/null 2>&1
%endif
exit 0

%post
%ifos linux
/sbin/ldconfig
if [ -f /var/lib/rpm/packages.rpm ]; then
    /bin/chown rpm.rpm /var/lib/rpm/*.rpm
elif [ -f /var/lib/rpm/Packages ]; then
    # undo db1 configuration
    rm -f /etc/rpm/macros.db1
    /bin/chown rpm.rpm /var/lib/rpm/[A-Z]*
else
    # initialize db3 database
    rm -f /etc/rpm/macros.db1
    /bin/rpm --initdb
fi
%endif
exit 0

%ifos linux
%postun
/sbin/ldconfig
if [ $1 = 0 ]; then
    /usr/sbin/userdel rpm
    /usr/sbin/groupdel rpm
fi


%post devel -p /sbin/ldconfig
%postun devel -p /sbin/ldconfig

%post -n popt -p /sbin/ldconfig
%postun -n popt -p /sbin/ldconfig
%endif

%if %{with_python_subpackage}
%post python -p /sbin/ldconfig
%postun python -p /sbin/ldconfig
%endif

%define	rpmattr		%attr(0755, rpm, rpm)

%files
%defattr(-,root,root)
%doc RPM-PGP-KEY RPM-GPG-KEY CHANGES GROUPS doc/manual/[a-z]*
%attr(0755, rpm, rpm)	/bin/rpm

%ifos linux
%config(noreplace,missingok)	/etc/cron.daily/rpm
%config(noreplace,missingok)	/etc/logrotate.d/rpm
%dir				/etc/rpm
%config(noreplace,missingok)	/etc/rpm/macros.*
%attr(0755, rpm, rpm)	%dir /var/lib/rpm

%define	rpmdbattr %attr(0644, rpm, rpm) %verify(not md5 size mtime) %ghost %config(missingok,noreplace)
%rpmdbattr	/var/lib/rpm/Basenames
%rpmdbattr	/var/lib/rpm/Conflictname
%rpmdbattr	/var/lib/rpm/__db.0*
%rpmdbattr	/var/lib/rpm/Dirnames
%rpmdbattr	/var/lib/rpm/Filemd5s
%rpmdbattr	/var/lib/rpm/Group
%rpmdbattr	/var/lib/rpm/Installtid
%rpmdbattr	/var/lib/rpm/Name
%rpmdbattr	/var/lib/rpm/Packages
%rpmdbattr	/var/lib/rpm/Providename
%rpmdbattr	/var/lib/rpm/Provideversion
%rpmdbattr	/var/lib/rpm/Removetid
%rpmdbattr	/var/lib/rpm/Requirename
%rpmdbattr	/var/lib/rpm/Requireversion
%rpmdbattr	/var/lib/rpm/Sigmd5
%rpmdbattr	/var/lib/rpm/Sha1header
%rpmdbattr	/var/lib/rpm/Triggername

%endif

%rpmattr	%{__prefix}/bin/rpm2cpio
%rpmattr	%{__prefix}/bin/gendiff
%rpmattr	%{__prefix}/bin/rpmdb
#%rpmattr	%{__prefix}/bin/rpm[eiu]
%rpmattr	%{__prefix}/bin/rpmsign
%rpmattr	%{__prefix}/bin/rpmquery
%rpmattr	%{__prefix}/bin/rpmverify

%{__prefix}/lib/librpm-4.1.so
%{__prefix}/lib/librpmdb-4.1.so
%{__prefix}/lib/librpmio-4.1.so
%{__prefix}/lib/librpmbuild-4.1.so

%attr(0755, rpm, rpm)	%dir %{__prefix}/lib/rpm
%rpmattr	%{__prefix}/lib/rpm/config.guess
%rpmattr	%{__prefix}/lib/rpm/config.sub
%rpmattr	%{__prefix}/lib/rpm/convertrpmrc.sh
%attr(0644, rpm, rpm)	%{__prefix}/lib/rpm/macros
%rpmattr	%{__prefix}/lib/rpm/mkinstalldirs
%rpmattr	%{__prefix}/lib/rpm/rpm.*
%rpmattr	%{__prefix}/lib/rpm/rpm2cpio.sh
%rpmattr	%{__prefix}/lib/rpm/rpm[deiukqv]
%attr(0644, rpm, rpm)	%{__prefix}/lib/rpm/rpmpopt*
%attr(0644, rpm, rpm)	%{__prefix}/lib/rpm/rpmrc

%ifarch i386 i486 i586 i686 athlon
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/i[3456]86*
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/athlon*
%endif
%ifarch alpha alphaev5 alphaev56 alphapca56 alphaev6 alphaev67
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/alpha*
%endif
%ifarch sparc sparcv9 sparc64
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/sparc*
%endif
%ifarch ia64
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/ia64*
%endif
%ifarch powerpc ppc ppciseries ppcpseries ppcmac
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/ppc*
%endif
%ifarch s390 s390x
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/s390*
%endif
%ifarch armv3l armv4l
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/armv[34][lb]*
%endif
%ifarch mips mipsel mipseb
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/mips*
%endif
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/noarch*

%lang(cs)	%{__prefix}/*/locale/cs/LC_MESSAGES/rpm.mo
%lang(da)	%{__prefix}/*/locale/da/LC_MESSAGES/rpm.mo
%lang(de)	%{__prefix}/*/locale/de/LC_MESSAGES/rpm.mo
%lang(fi)	%{__prefix}/*/locale/fi/LC_MESSAGES/rpm.mo
%lang(fr)	%{__prefix}/*/locale/fr/LC_MESSAGES/rpm.mo
%lang(is)	%{__prefix}/*/locale/is/LC_MESSAGES/rpm.mo
%lang(ja)	%{__prefix}/*/locale/ja/LC_MESSAGES/rpm.mo
%lang(ko)	%{__prefix}/*/locale/ko/LC_MESSAGES/rpm.mo
%lang(no)	%{__prefix}/*/locale/no/LC_MESSAGES/rpm.mo
%lang(pl)	%{__prefix}/*/locale/pl/LC_MESSAGES/rpm.mo
%lang(pt)	%{__prefix}/*/locale/pt/LC_MESSAGES/rpm.mo
%lang(pt_BR)	%{__prefix}/*/locale/pt_BR/LC_MESSAGES/rpm.mo
%lang(ro)	%{__prefix}/*/locale/ro/LC_MESSAGES/rpm.mo
%lang(ru)	%{__prefix}/*/locale/ru/LC_MESSAGES/rpm.mo
%lang(sk)	%{__prefix}/*/locale/sk/LC_MESSAGES/rpm.mo
%lang(sl)	%{__prefix}/*/locale/sl/LC_MESSAGES/rpm.mo
%lang(sr)	%{__prefix}/*/locale/sr/LC_MESSAGES/rpm.mo
%lang(sv)	%{__prefix}/*/locale/sv/LC_MESSAGES/rpm.mo
%lang(tr)	%{__prefix}/*/locale/tr/LC_MESSAGES/rpm.mo

%{__prefix}%{__share}/man/man1/gendiff.1*
%{__prefix}%{__share}/man/man8/rpm.8*
%{__prefix}%{__share}/man/man8/rpm2cpio.8*
%lang(pl)	%{__prefix}%{__share}/man/pl/man[18]/*.[18]*
%lang(ru)	%{__prefix}%{__share}/man/ru/man[18]/*.[18]*
%lang(sk)	%{__prefix}%{__share}/man/sk/man[18]/*.[18]*

%files build
%defattr(-,root,root)
%dir %{__prefix}/src/redhat
%dir %{__prefix}/src/redhat/BUILD
%dir %{__prefix}/src/redhat/SPECS
%dir %{__prefix}/src/redhat/SOURCES
%dir %{__prefix}/src/redhat/SRPMS
%dir %{__prefix}/src/redhat/RPMS
%{__prefix}/src/redhat/RPMS/*
%rpmattr	%{__prefix}/bin/rpmbuild
%rpmattr	%{__prefix}/lib/rpm/brp-*
%rpmattr	%{__prefix}/lib/rpm/check-prereqs
%rpmattr	%{__prefix}/lib/rpm/config.site
%rpmattr	%{__prefix}/lib/rpm/cpanflute
%rpmattr	%{__prefix}/lib/rpm/cpanflute2
%rpmattr	%{__prefix}/lib/rpm/cross-build
%rpmattr	%{__prefix}/lib/rpm/find-lang.sh
%rpmattr	%{__prefix}/lib/rpm/find-prov.pl
%rpmattr	%{__prefix}/lib/rpm/find-provides
%rpmattr	%{__prefix}/lib/rpm/find-provides.perl
%rpmattr	%{__prefix}/lib/rpm/find-req.pl
%rpmattr	%{__prefix}/lib/rpm/find-requires
%rpmattr	%{__prefix}/lib/rpm/find-requires.perl
%rpmattr	%{__prefix}/lib/rpm/get_magic.pl
%rpmattr	%{__prefix}/lib/rpm/getpo.sh
%rpmattr	%{__prefix}/lib/rpm/http.req
%rpmattr	%{__prefix}/lib/rpm/javadeps
%rpmattr	%{__prefix}/lib/rpm/magic.prov
%rpmattr	%{__prefix}/lib/rpm/magic.req
%rpmattr	%{__prefix}/lib/rpm/perl.prov
%rpmattr	%{__prefix}/lib/rpm/Specfile.pm

# XXX remove executable bit to disable autogenerated perl requires for now.
%rpmattr	%{__prefix}/lib/rpm/perl.req
#%attr(0644, rpm, rpm) %{__prefix}/lib/rpm/perl.req

%rpmattr	%{__prefix}/lib/rpm/rpm[bt]
%rpmattr	%{__prefix}/lib/rpm/rpmdiff
%rpmattr	%{__prefix}/lib/rpm/rpmdiff.cgi
%rpmattr	%{__prefix}/lib/rpm/trpm
%rpmattr	%{__prefix}/lib/rpm/u_pkg.sh
%rpmattr	%{__prefix}/lib/rpm/vpkg-provides.sh
%rpmattr	%{__prefix}/lib/rpm/vpkg-provides2.sh

%{__prefix}%{__share}/man/man8/rpmbuild.8*

%if %{with_python_subpackage}
%files python
%defattr(-,root,root)
%{__prefix}/lib/python%{with_python_version}/site-packages/rpmmodule.so
#%{__prefix}/lib/python%{with_python_version}/site-packages/poptmodule.so
%endif

%if %{with_perl_subpackage}
%files perl
%defattr(-,root,root)
%rpmattr	%{__prefix}/bin/rpmprune
%{perl_sitearch}/auto/*
%{perl_sitearch}/RPM
%{perl_sitearch}/RPM.pm
%{__prefix}%{__share}/man/man1/rpmprune.1*
%{__prefix}%{__share}/man/man3/RPM*
%endif

%files devel
%defattr(-,root,root)
%if %{with_apidocs}
%doc apidocs
%endif
%{__prefix}/include/rpm
%{__prefix}/lib/librpm.a
%{__prefix}/lib/librpm.la
%{__prefix}/lib/librpm.so
%{__prefix}/lib/librpmdb.a
%{__prefix}/lib/librpmdb.la
%{__prefix}/lib/librpmdb.so
%{__prefix}/lib/librpmio.a
%{__prefix}/lib/librpmio.la
%{__prefix}/lib/librpmio.so
%{__prefix}/lib/librpmbuild.a
%{__prefix}/lib/librpmbuild.la
%{__prefix}/lib/librpmbuild.so

%files -n popt
%defattr(-,root,root)
%{__prefix}/lib/libpopt.so.*
%{__prefix}%{__share}/man/man3/popt.3*
%lang(cs)	%{__prefix}/*/locale/cs/LC_MESSAGES/popt.mo
%lang(da)	%{__prefix}/*/locale/da/LC_MESSAGES/popt.mo
%lang(gl)	%{__prefix}/*/locale/gl/LC_MESSAGES/popt.mo
%lang(hu)	%{__prefix}/*/locale/hu/LC_MESSAGES/popt.mo
%lang(is)	%{__prefix}/*/locale/is/LC_MESSAGES/popt.mo
%lang(ko)	%{__prefix}/*/locale/ko/LC_MESSAGES/popt.mo
%lang(no)	%{__prefix}/*/locale/no/LC_MESSAGES/popt.mo
%lang(pt)	%{__prefix}/*/locale/pt/LC_MESSAGES/popt.mo
%lang(ro)	%{__prefix}/*/locale/ro/LC_MESSAGES/popt.mo
%lang(ru)	%{__prefix}/*/locale/ru/LC_MESSAGES/popt.mo
%lang(sk)	%{__prefix}/*/locale/sk/LC_MESSAGES/popt.mo
%lang(sl)	%{__prefix}/*/locale/sl/LC_MESSAGES/popt.mo
%lang(sv)	%{__prefix}/*/locale/sv/LC_MESSAGES/popt.mo
%lang(tr)	%{__prefix}/*/locale/tr/LC_MESSAGES/popt.mo
%lang(uk)	%{__prefix}/*/locale/uk/LC_MESSAGES/popt.mo
%lang(wa)	%{__prefix}/*/locale/wa/LC_MESSAGES/popt.mo
%lang(zh_CN)	%{__prefix}/*/locale/zh_CN.GB2312/LC_MESSAGES/popt.mo

# XXX These may end up in popt-devel but it hardly seems worth the effort now.
%{__prefix}/lib/libpopt.a
%{__prefix}/lib/libpopt.la
%{__prefix}/lib/libpopt.so
%{__prefix}/include/popt.h

%changelog
* Sat Apr 13 2002 Jeff Johnson <jbj@redhat.com> 4.1-0.07
- merge conflicts into problems, handle as transaction set variable.

* Fri Apr 12 2002 Jeff Johnson <jbj@redhat.com> 4.1-0.06
- use rpmdb-redhat to suggest dependency resolution(s).

* Thu Apr 11 2002 Jeff Johnson <jbj@redhat.com> 4.1-0.05
- rescusitate --rebuild.

* Wed Apr 10 2002 Jeff Johnsion <jbj@redhat.com> 4.1-0.04
- beecrypt: add types.h, eliminate need for config.gnu.h.

* Sat Mar 16 2002 Jeff Johnson <jbj@redhat.com>
- *really* dump signature header immutable region.

* Sun Mar 10 2002 Jeff Johnson <jbj@redhat.com>
- make --addsign and --resign behave exactly the same.
- splint annotationsm, signature cleanup.
- drill ts/fi through verify mode, add methods to keep fi abstract.
- use mmap when calculating file digests on verify, ~20% faster.
- permit --dbpath and --root with signature (i.e. --import) modes.
