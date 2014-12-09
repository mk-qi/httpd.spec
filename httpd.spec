# httpd.spec
# by mk-qi 
# Contact  root@mkrss.com
# only works for apache2 
#
# --------------------------------
# this build will install apache2
# to /usr/local/apache2/
#--------------------------------

%define prefix /usr/local/apache2/
%define contentdir /usr/local/apache2/htdocs
%define mmn 20051115
%define ver 2.2.29

# no debug packages
%define debug_package %{nil}

Summary: Apache HTTP Server
Name: httpd
Version: %{ver}
Release: fanli%{?dist}
URL: http://httpd.apache.org/
Vendor: Apache Software Foundation
License: Apache License, Version 2.0
Group: System Environment/Daemons


BuildRoot: %{_tmppath}/%{name}-root
BuildRequires: perl, pkgconfig, findutils
BuildRequires: zlib-devel

#Requires: initscripts >= 8.36
Obsoletes: httpd-suexec
Requires(pre): /sbin/chkconfig, /bin/mktemp, /bin/rm, /bin/mv
Requires(pre): sh-utils, textutils, /usr/sbin/useradd

Provides: webserver
Provides: httpd-mmn = %{mmn}

Conflicts: pcre < 4.0
Source0: http://www.apache.org/dist/httpd/httpd-%{version}.tar.bz2
#patches refer to http://www.apache.org/dist/httpd/patches/


%description

%package manual
Group: Documentation
Summary: Documentation for the Apache HTTP server.
%description manual

%package devel
Group: Development/Libraries
Summary: Development tools for the Apache HTTP server.
Requires: httpd = %{version}-%{release}

%description devel

%prep
%setup -q
%build

CFLAGS="$RPM_OPT_FLAGS -fno-strict-aliasing"
SH_LDFLAGS="-Wl,-z,relro"
export CFLAGS SH_LDFLAGS

# Hard-code path to links to avoid unnecessary builddep
export LYNX_PATH=/usr/bin/links

function mpmbuild()
{
mpm=$1; shift
mkdir $mpm; pushd $mpm
../configure -C \
        --prefix=/usr/local/apache2 \
        --enable-static-support \
        --enable-static-htpasswd \
        --enable-static-htdigest \
        --enable-static-rotatelogs \
        --enable-static-logresolve \
        --enable-static-ab \
        --enable-static-checkgid \
        --enable-mime-magic=static \
        --enable-expires=static \
        --enable-headers=static \
        --enable-usertrack=static \
        --enable-unique-id=static \
        --enable-deflate=static \
        --enable-rewrite=static \
        --enable-mime=static \
        --enable-status=static \
        --enable-log-config=static \
        --enable-mods-shared=most \
        --enable-authz-host=static \
        --enable-dir \
        --enable-so \
        --enable-mods-shared="version env setenvif \
        deflate info rewrite headers cache mem_cache file_cache disk_cache \
        authz-host log-config proxy proxy-connect \
        proxy-http proxy-ftp alias userdir mime asis \
        negotiation actions authn_file authn_default \
        authz_groupfile authz_user authz_default auth_basic \
        autoindex include filter env setenvi dav dav-fs" \
        $*
 
make -j 24  %{?_smp_mflags}
popd
}

# Build everything and the kitchen sink with the prefork build
mpmbuild prefork 

%install
rm -rf $RPM_BUILD_ROOT

pushd prefork
make DESTDIR=$RPM_BUILD_ROOT install
popd

cp -rf  $RPM_BUILD_ROOT%{prefix}/conf/httpd.conf \
 	$RPM_BUILD_ROOT%{prefix}/conf/httpd.conf.orig \

cp -rf  $RPM_SOURCE_DIR/vhosts \
        $RPM_BUILD_ROOT%{prefix}/conf/

# Make the MMN accessible to module packages
echo %{mmn} > $RPM_BUILD_ROOT%{prefix}/include/.mmn

# docroot
install -m 644 $RPM_SOURCE_DIR/index.html \
	$RPM_BUILD_ROOT%{contentdir}/index.html

install -m 644 $RPM_SOURCE_DIR/httpd.conf \
        $RPM_BUILD_ROOT%{prefix}/conf/httpd.conf

# install SYSV init stuff
mkdir -p $RPM_BUILD_ROOT/etc/rc.d/init.d

install -m755 $RPM_SOURCE_DIR/httpd.init \
	$RPM_BUILD_ROOT/etc/rc.d/init.d/httpd


# Remove unpackaged files
rm -f $RPM_BUILD_ROOT%{prefix}/lib/*.exp \
      $RPM_BUILD_ROOT%{prefix}/modules/*.exp \
      $RPM_BUILD_ROOT%{contentdir}/cgi-bin/*

rm -rf $RPM_BUILD_ROOT%{prefix}/conf/original
rm -rf $RPM_BUILD_ROOT%{prefix}/{ABOUT_APACHE,README,CHANGES,LICENSE,VERSIONING,NOTICE}


%pre
# Add the daemon user
/usr/sbin/useradd -c daemon -u 48 \
        -s /sbin/nologin -r -d %{contentdir} daemon 2> /dev/null || :
 
%triggerpostun -- daemon < 2.0
/sbin/chkconfig --add httpd

%post
# Register the httpd service
/sbin/chkconfig --add httpd
/etc/init.d/httpd start > /dev/null 2>&1

# Export apache bin path
sed -i /^'export PATH USER'/a\\'export PATH=$PATH:/usr/local/apache2/bin' /etc/profile
. /etc/profile


%preun
if [ $1 = 0 ]; then
	/sbin/service httpd stop > /dev/null 2>&1
	/sbin/chkconfig --del httpd
fi


#Unexport path for apache
sed  -i '/\/usr\/local\/apache2\/bin/d' /etc/profile
. /etc/profile

%check
# Check the built modules are all PIC
if readelf -d $RPM_BUILD_ROOT%{prefix}/modules/*.so | grep TEXTREL; then
   : modules contain non-relocatable code
   exit 1
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)

%{prefix}/bin
%{prefix}/conf
%dir %{prefix}/logs
%{prefix}/conf/vhosts
%{prefix}/modules

%{prefix}/lib
%{prefix}/icons
%{prefix}/error
%{prefix}/htdocs
%config %{_sysconfdir}/rc.d/init.d/httpd

%files manual
%defattr(-,root,root)
%config %{prefix}/conf/extra/httpd-manual.conf
%{prefix}/error/README
%{prefix}/manual/*
%{prefix}/man/*

%files devel
%defattr(-,root,root)
%{prefix}/bin/apxs
%{prefix}/bin/checkgid
%{prefix}/bin/dbmmanage
%{prefix}/bin/envvars*
%{prefix}/build
%{prefix}/include
%{prefix}/cgi-bin

%changelog
