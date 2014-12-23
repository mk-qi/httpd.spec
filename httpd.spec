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
%define contentdir /usr/local/webdata/root/
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

%description


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
        --enable-authz-host=static \
        --enable-dir=static \
        --enable-so \
        $*
 
make -j 24  %{?_smp_mflags}
popd
}

# Build everything and the kitchen sink with the prefork build
mpmbuild prefork --disable-shared \
         --disable-version \
         --disable-info \
         --disable-cache \
         --disable-mem_cache \
         --disable-file_cache \
         --disable-disk_cache \
         --disable-proxy \
         --disable-proxyconnect \
         --disable-proxyhttp \
         --disable-proxyftp \
         --disable-alias \
         --disable-userdir \
         --disable-mime \
         --disable-asis \
         --disable-negotiation \
         --disable-actions \
         --disable-authn_file \
         --disable-authn_default \
         --disable-authz_groupfile \
         --disable-authz_user \
         --disable-authz_default \
         --disable-auth_basic \
         --disable-autoindex \
         --disable-include \
         --disable-cgi \
         --disable-cgid \
         --disable-filter \
         --disable-dav \
         --disable-davfs \

%install
rm -rf $RPM_BUILD_ROOT

pushd prefork
make DESTDIR=$RPM_BUILD_ROOT install
popd

cp -rf  $RPM_BUILD_ROOT%{prefix}/conf/httpd.conf \
 	$RPM_BUILD_ROOT%{prefix}/conf/httpd.conf.orig \

if [ -d  $RPM_SOURCE_DIR/vhosts ];then
cp -rf  $RPM_SOURCE_DIR/vhosts \
        $RPM_BUILD_ROOT%{prefix}/conf/
fi

mkdir -p $RPM_BUILD_ROOT%{prefix}/conf/vhosts
mkdir -p $RPM_BUILD_ROOT%{contentdir}

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
rm -rf $RPM_BUILD_ROOT%{prefix}/lib/*.exp \
      $RPM_BUILD_ROOT%{prefix}/modules/*.exp \
      $RPM_BUILD_ROOT%{prefix}/cgi-bin/* \
      $RPM_BUILD_ROOT%{prefix}/bin/apxs \
      $RPM_BUILD_ROOT%{prefix}/bin/apr-1-config \
	$RPM_BUILD_ROOT%{prefix}/bin/apu-1-config \
	$RPM_BUILD_ROOT%{prefix}/bin/checkgid \
	$RPM_BUILD_ROOT%{prefix}/bin/dbmmanage \
	$RPM_BUILD_ROOT%{prefix}/bin/envvars \
	$RPM_BUILD_ROOT%{prefix}/bin/envvars-std \
	$RPM_BUILD_ROOT%{prefix}/bin/htdbm \
	$RPM_BUILD_ROOT%{prefix}/bin/htdigest \
	$RPM_BUILD_ROOT%{prefix}/bin/httxt2dbm \
	$RPM_BUILD_ROOT%{prefix}/bin/logresolve \
	$RPM_BUILD_ROOT%{prefix}/bin/rotatelogs \
	$RPM_BUILD_ROOT%{prefix}/build \
	$RPM_BUILD_ROOT%{prefix}/include \
	$RPM_BUILD_ROOT%{prefix}/icons \
	$RPM_BUILD_ROOT%{prefix}/lib \
	$RPM_BUILD_ROOT%{prefix}/error \

      

rm -rf $RPM_BUILD_ROOT%{prefix}/conf/original
rm -rf $RPM_BUILD_ROOT%{prefix}/{ABOUT_APACHE,README,CHANGES,LICENSE,VERSIONING,NOTICE}
#
rm -rf $RPM_BUILD_ROOT%{prefix}/{man,manual}
rm -rf $RPM_BUILD_ROOT%{prefix}/conf/extra/httpd-manual.conf


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

%{prefix}/bin/htcacheclean
%{prefix}/bin/httpd
%{prefix}/bin/apachectl
%{prefix}/bin/ab
%{prefix}/bin/htpasswd


%{prefix}/conf
%dir %{prefix}/logs
%{prefix}/modules
%{contentdir}/index.html

#%{prefix}/lib
#%{prefix}/icons
#%{prefix}/error
%{prefix}/htdocs
%config %{_sysconfdir}/rc.d/init.d/httpd
#%{prefix}/build
#%{prefix}/include

%changelog
