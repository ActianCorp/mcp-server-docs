#!/bin/bash
#  Copyright (c) 2005, 2021 Actian Corporation. All rights reserved.
#
#  Name: express_install.sh -- Single point install script.
#	 (also client_install.sh)
#
#  Usage:
#       See usage() below
#
#  Description:
#	Installs product quickly with default values.
#
#  Exit Status:
#	0	Installation procedure completed.
#	1	Not run as root
#	2	Invalid Installation ID
#	3	Invalid installation path
#	5	Installation failed
#	6	Upgrade not supported
#	10	Invalid argument
#
#	Also see platform specific routines
#
#
# Multi-platform whoami
#
iiwhoami()
{
if [ -f /usr/ucb/whoami ]; then
	/usr/ucb/whoami
elif [ -f /usr/bin/whoami ]; then
	/usr/bin/whoami
elif [ -f /usr/bin/id ]; then
	IFS="()"
	set - `/usr/bin/id`
	echo $2
elif [ -f /bin/id ]; then
	IFS="()"
	set - `/bin/id`
	echo $2
else
	touch /tmp/who$$
	set - `ls -l /tmp/who$$`
	echo $3
	rm -f /tmp/who$$
fi
}

set_lib_path()
{
    unames=`uname -s`
    unamem=`uname -m`
    case $unames in
        HP-UX)
            case $unamem in
                ia64)
                    if [ "$SHLIB_PATH" ] ; then
                        SHLIB_PATH=$II_SYSTEM/ingres/lib/lp32:$SHLIB_PATH
                    else
                        SHLIB_PATH=/lib:/usr/lib:$II_SYSTEM/ingres/lib/lp32
                    fi
                    export SHLIB_PATH
                    if [ "$LD_LIBRARY_PATH" ] ; then
                        LD_LIBRARY_PATH=$II_SYSTEM/ingres/lib:$LD_LIBRARY_PATH
                    else
                        LD_LIBRARY_PATH=$II_SYSTEM/ingres/lib
                    fi
                    export LD_LIBRARY_PATH
                    ;;
                *)
                    if [ "$SHLIB_PATH" ] ; then
                        SHLIB_PATH=$II_SYSTEM/ingres/lib:$SHLIB_PATH
                    else
                        SHLIB_PATH=/lib:/usr/lib:$II_SYSTEM/ingres/lib
                    fi
                    export SHLIB_PATH
                    if [ "$LD_LIBRARY_PATH" ] ; then
                        LD_LIBRARY_PATH=$II_SYSTEM/ingres/lib/lp64:$LD_LIBRARY_PATH
                    else
                        LD_LIBRARY_PATH=$II_SYSTEM/ingres/lib/lp64
                    fi
                    export LD_LIBRARY_PATH
                    ;;
            esac
            ;;
        AIX)
            if [ "$LIBPATH" ] ; then
                LIBPATH=$II_SYSTEM/ingres/lib:$II_SYSTEM/ingres/lib/lp64:$LIBPATH
            else
                LIBPATH=/lib:/usr/lib:$II_SYSTEM/ingres/lib:$II_SYSTEM/ingres/lib/lp64
            fi
            export LIBPATH
            ;;
	Darwin)
            if [ "$DYLD_LIBRARY_PATH" ] ; then
                DYLD_LIBRARY_PATH=$II_SYSTEM/ingres/lib:$DYLD_LIBRARY_PATH
            else
                DYLD_LIBRARY_PATH=/lib:/usr/lib:$II_SYSTEM/ingres/lib
            fi
            export DYLD_LIBRARY_PATH
	    ;;
        *)
            if [ "$LD_LIBRARY_PATH" ] ; then
                LD_LIBRARY_PATH=$II_SYSTEM/ingres/lib:$LD_LIBRARY_PATH
            else
                LD_LIBRARY_PATH=/lib:/usr/lib:$II_SYSTEM/ingres/lib
            fi
                export LD_LIBRARY_PATH
            if [ "$LD_LIBRARY_PATH_64" ] ; then
                LD_LIBRARY_PATH_64=$II_SYSTEM/ingres/lib/lp64:$LD_LIBRARY_PATH_64
            else
                LD_LIBRARY_PATH_64=$II_SYSTEM/ingres/lib/lp64
            fi
                export LD_LIBRARY_PATH_64
            ;;
    esac
}

have_x100_server()
{
    [ "${unames}" = "Linux" ] && [ "${clipkg}" != "true" ] && [ "${prod_name}" = "Actian Ingres" -o "${vwinst}" = "true" ]
}

usage()
{
    cat << EOF
usage:

    $self [-interactive|-express] [-acceptlicense]
EOF
    [ "${uidflag}${userflag}${noroot_flag}${leaderonlyflag}${demo_flag}" ] &&
	cat << EOF
	 ${uidflag}${userflag}${noroot_flag}${leaderonlyflag}${demo_flag}
EOF
    if [ "$unames" = "Linux" -a "${clipkg}" != "true" ] ; then
	cat << EOF
	 [-withad|-noad]
EOF
    fi
    if $rhybrid ; then
        cat << EOF
         [-no32bit]
EOF
    fi
    cat << EOF
	 [-respfile file] [-?|-help] [instance_ID] [install_dir]
EOF
    if $licinst ; then
        cat << EOF
         [-licdir dir]
EOF
    fi
	if [ "${vhinst}" != "true" -a "$short_name" != "Actian" -a "$unames" = "Linux" ]; then
        cat << EOF
         [-sparkdownload] [-hadoopdownload] [-gcscdownload] [-udfcdownload]
         [-tflowdownload]
EOF
	fi
    cat << EOF
	 -respfile file Provide the absolute path to the response file used when
		        running setup. A response file lets you customize
			the installation. (Requires -express or -acceptlicense,
			not valid with -interactive.)
EOF
    if $licinst ; then
    cat << EOF
         -licdir dir    Use 'dir' as the location of a valid license.xml
                        file. (Not valid with -respfile.)
EOF
    fi
    if [ "${userflag}" ] ; then
	cat << EOF
         -user username Installs as username instead of actian.
			The username must exist. (Disallowed with -noroot.)
         -uid uid	Specify uid to be used when creating the user.
			The username must exist. (Disallowed with -noroot.)
         -noroot	Installs Actian Client as the current user.
			All installation locations must exist
			and be writable by the current user for the
			installation to succeed.
			The instance will be owned by the current user.
                        Installation owner cannot be changed with -user or II_USERID.
         -usesudo	Installs Actian Client using the current user
			and invokes sudo for root access, locally and
			remotely. The instance is owned as "actian" by
			default. If required, the current user is used
			for remote connections and sudo is invoked for
			root access. (Not valid for the 'root' user.)
                        Installation owner can be changed with -user or II_USERID.
EOF
	if $vhinst ; then
	     cat << EOF
			NOTE: Cluster topology may not be visible as
			current user so workers file may not be generated.
			In that case, default worker file is created
			containing only Leader node.
EOF
	fi
    fi
    if [ "$unames" = "Linux" -a "${clipkg}" != "true" ] ; then
	cat << EOF
         -with/noad	Install/exclude Actian Director.
EOF
	if [ "${demo_flag}" ] ; then
	    cat << EOF
         -with/nodemo	Install/exclude Demo packages.
EOF
	fi
    fi
    if [ "${leaderonlyflag}" ] ; then
	cat << EOF
         -leaderonly	Sets up leader node only; no worker nodes are set up.
			(No remote connections attempted.)
EOF
    fi
    if $rhybrid ; then
        cat << EOF
         -no32bit       Skip installing 32 bit support and ABF packages.
			(Not valid with -interactive.)
EOF
    fi
       cat << EOF
         -acceptlicense	Accepts all license prompts.
         -express	Express install, no user prompts. (Implies
			-acceptlicense, conflicts with -interactive.)
                        requires -licdir or -respfile
         -interactive	Interactive install, prompts for all configuration
			options.
			(For advanced users only. Conflicts with -express.)
EOF
    if [ "$licinst" = "true" -a "$tarpkg" = "true" ] ; then
        case "$short_name" in
            Actian|Ingres)
                cat << EOF
                        NOTE: -interactive cannot be combined with
                        -acceptlicense.
EOF
                ;;
            Vector*)
                cat << EOF
                        NOTE: -interactive also requires -licdir.
EOF
                ;;
            *)
                ;;
        esac
    fi
    if [ "$tarpkg" = "false" ] ; then
    cat << EOF
			NOTE: There is only limited prompting
 			for RPM and DEBs installs. For full control a
			response file must be used.
EOF
    fi
    cat << EOF
         instance_ID	Defines a two-character string where the first
			character must be an uppercase letter and the second
			character must be an uppercase letter or a number from
			0 to 9.
         install_dir	Full path to the location where ${prod_name} is to be
			installed (II_SYSTEM).
			Default: $definst
			Note: Not valid for DEBs, which are hard coded to:
EOF
		if [ "$short_name" = "Actian" ] ; then
			cat << EOF
			${definst}
EOF
		else
			cat << EOF
			/opt/Actian/${short_name}
EOF
		fi

	if [ "${vhinst}" != "true" -a "$short_name" != "Actian" -a "$unames" = "Linux" ];then
	cat << EOF
        -sparkdownload  Download and configure Spark Container Image.
			(Not valid with -interactive or -respfile.)
        -hadoopdownload Download and configure Apache Hadoop to access
			remote file systems like AWS.
			(Not valid with -interactive or -respfile.)
        -gcscdownload   Download and configure Google Cloud Storage
			Connector. Requires Apache Hadoop to be installed.
			(Not valid with -interactive or -respfile.)
        -udfcdownload   Download and enable UDF Container Image.
			(Not valid with -interactive or -respfile.)
        -tflowdownload  Download and enable Tensorflow Container Image.
			(Not valid with -interactive or -respfile.)
EOF

	fi

}

#
# For signed builds, use script to validate GPG package signatures
# If we can't prompt for continue

#
validate_signature()
{
    $rpmpkg && pkgdir=${rootdir}/rpm
    $debpkg && pkgdir=${rootdir}/apt
    ${checksig} ${pkgdir}
    rc=$?

    if [ $rc = 0 ]
    then
	return
    elif [ $rc = 10 ]
    then
	while true
	do
        printf "Do you wish to continue? (y/n): "
        read ans
	    case "$ans" in
		[Yy]| \
		[Yy][Ee][Ss])
		    # RPM bails by default if we don't tell it not to
		    $rpmpkg && allow_unauth=--nosignature
		    $debpkg && signrelease=false
		    return
		    ;;
		[Nn]| \
		[Nn][Oo])
		    exit 1
		    ;;
		*)
		    continue
		    ;;
	    esac
	done
    else
	exit 1
    fi
}

validate_path()
{
   # Takes path as argument
   # if there is more or less than one argument
   # path contains space
   [ $# = 1 ] &&
       echo $1 | grep '^/' > /dev/null
}

# for 64 bit installes we need LIBC 32 bit to run ABF
# this will check whether the installer can find them
# and error out if not available.
check_libc32()
{
    found_libc32=false

    if $no32bit || [ "${rhybrid}" != "true" ] ; then
	return 0 #no need to check
    fi

    archtst=$rootdir/bin/iiarchtst
    # First we try to run iiarchtst
    if command -v $archtst >> /dev/null ; then
        $archtst >> /dev/null 2>&1
        archrc=$?
        if [ $archrc = 0 ]; then
            # 32bit ok, no need to run any other tests
            found_libc32=true
        fi
    fi

    if [ "${interactive}" = "true"  -a $found_libc32 != "true" ] ; then
        cat << EOF
Couldn't find the required 32 bit LIBC libraries.
Please install these libraries for 32 bit support.
EOF

        while true
        do
        printf "Do you wish to continue? (y/n): "
        read ans
        case "$ans" in
            [Yy]| \
            [Yy][Ee][Ss])
            break
            ;;
            [Nn]| \
            [Nn][Oo])
            exit 1
            ;;
            *)
            continue
            ;;
        esac
        done


    else
        $found_libc32 || {
            cat << EOF
Couldn't find the required 32 bit LIBC libraries.
Please install these libraries or exclude the installation
of 32 bit support with the -no32bit flag.
EOF
            exit 1
        }
    fi
}

accept_java_license()
{
    # Java license
    if [ "${licaccept}" != "true" ] ; then
	# Java license
	[ -f $rootdir/LICENSE.java ] &&
	{
	    cat << EOF
A Java Runtime Environment (JRE) is installed as part of

    $brand_name $prod_rel

EOF
	    # we ship JCE for Vector H and Ingres on 64bit Linux
	    [ $do_jce = "true" ] && cat << EOF
which includes the Unlimited Strength Jurisdiction Policy
files for the Java Cryptography Extension (JCE).

`cat $rootdir/LICENSE.java`

EOF

	    cat << EOF
To accept the license agreement and continue with
the installation answer 'y'.

To reject the license agreement and abort the
installation answer 'n'.

EOF
	    while true
	    do
	    printf "Do you accept the Java license agreement? (y/n) [n] "
	    # check for redirected output
	    [ -t 1 ] || return 1
	    read ans
	    case "$ans" in
		[Yy]| \
		[Yy][Ee][Ss])
		    echo
		    break
		    ;;
                ""| \
                [Nn]| \
                [Nn][Oo])
                    return 1
                    ;;
                *)
                    continue
                    ;;

	    esac
	    done
	}
    fi

    return 0
}

cp_lic()
{
    if [ "$usesudo" = "true" ] ; then
        if [ -f ${instloc}/ingres/LICENSE ] ; then
            sudo -u $ingusr rm -f ${instloc}/ingres/LICENSE
        fi
        if [ -f ${instloc}/ingres/THIRDPARTYNOTICES.TXT ]; then
            sudo -u $ingusr rm -f ${instloc}/ingres/THIRDPARTYNOTICES.TXT
        fi
        if [ -f ${licfile} ] ; then
            sudo -u $ingusr cp ${licfile} ${instloc}/ingres/ ||
               echo "WARNING: Error copying LICENSE file into place."
        fi
        if [ -f ${tpnfile} ] ; then
            sudo -u $ingusr cp ${tpnfile} ${instloc}/ingres/ ||
               echo "WARNING: Error copying THIRDPARTYNOTICES.TXT file into place."
        fi
        ## Copy attribution report file
        if [ -f ${rootdir}/${reportfile} -a $rc -eq 0 ] ; then
            sudo -u $ingusr cp ${rootdir}/${reportfile} ${instloc}/ingres/ ||
               echo "WARNING: Error copying ${reportfile} file into place."
        fi
    elif [ "$noroot" = "true" ] ; then
        if [ -f ${instloc}/ingres/LICENSE ] ; then
            sudo -u $ingusr rm -f ${instloc}/ingres/LICENSE
        fi
        if [ -f ${instloc}/ingres/THIRDPARTYNOTICES.TXT ]; then
            sudo -u $ingusr rm -f ${instloc}/ingres/THIRDPARTYNOTICES.TXT
        fi
        if [ -f ${licfile} ] ; then
            cp ${licfile} ${instloc}/ingres/ ||
               echo "WARNING: Error copying LICENSE file into place."
        fi
        if [ -f ${tpnfile} ] ; then
            cp ${tpnfile} ${instloc}/ingres/ ||
               echo "WARNING: Error copying THIRDPARTYNOTICES.TXT file into place."
        fi
        ## Copy attribution report file
        if [ -f ${rootdir}/${reportfile} -a $rc -eq 0 ] ; then
            cp ${rootdir}/${reportfile} ${instloc}/ingres/ ||
               echo "WARNING: Error copying ${reportfile} file into place."
        fi
    else
        if [ -f ${instloc}/ingres/LICENSE ] ; then
            rm -f ${instloc}/ingres/LICENSE
        fi
        if [ -f ${instloc}/ingres/THIRDPARTYNOTICES.TXT ]; then
            rm -f ${instloc}/ingres/THIRDPARTYNOTICES.TXT
        fi
        if [ -f ${licfile} ] ; then
            su $ingusr -c "cp ${licfile} ${instloc}/ingres/" ||
               echo "WARNING: Error copying LICENSE file into place."
        fi
        if [ -f ${tpnfile} ] ; then
            su $ingusr -c "cp ${tpnfile} ${instloc}/ingres/" ||
               echo "WARNING: Error copying THIRDPARTYNOTICES.TXT file into place."
        fi
        ## Copy attribution report file
        if [ -f ${rootdir}/${reportfile} -a $rc -eq 0 ] ; then
            su $ingusr -c "cp ${rootdir}/${reportfile} ${instloc}/ingres/" ||
               echo "WARNING: Error copying ${reportfile} file into place."
        fi
    fi
}

# Install director from tar archive
install_ad()
{
    ADVERS=2.4.4
    ADBLD=820
    ADPKG=director-${ADVERS}-${ADBLD}
    ADRPM=${ADPKG}.${RPMARCH}.rpm
    new_install=0

    if [ -f "${rootdir}/rpm/${ADRPM}" ] ; then
	cat << EOF
Installing Director...

EOF
	if rpm -q $ADPKG > /dev/null 2>&1 ; then
	    cat << EOF
$ADPKG is already installed.

EOF
	    rc=0
	else
	    $sudocmd rpm -Uvh "${rootdir}/rpm/${ADRPM}"
	    rc=$?
	    if [ $rc -eq 0 ] ; then
	        new_install=1
	    fi
	fi
    elif [ -d "$1" ] ; then
	# if director isn't in the saveset just exit
	tar tf $ingtar director > /dev/null 2>&1 || return 0

        instroot=`dirname $1`
        if [ -x /usr/bin/update-alternatives ] ; then
            alternatives=/usr/bin/update-alternatives
        else
            alternatives=/usr/sbin/update-alternatives
        fi
	makeactive=false

        cat << EOF
Installing Director...

EOF
	# check for existing installs if target location is empty
	[ -L /usr/bin/director ] &&
	{
	    adexe=`readlink -f /usr/bin/director 2> /dev/null`
	    if [ -x "$adexe" ] ; then
		addir=`dirname $adexe`
		if [ "$addir" != "${instroot}/Director" ] ; then
		    source $II_SYSTEM/ingres/utility/iishlib
    		    if $prompt ; then

			cat << EOF
Existing Director instance found under:

    $addir

EOF
			prompt "Replace it with Director ${ADVERS}-${ADBLD}?" y
			if [ $? = 0 ] ; then
			    instroot=`dirname $addir`
			    $sudocmd $alternatives --remove \
			        director ${instroot}/Director/director
			    makeactive=true
			fi
			echo
		    fi
		fi
	    else
		# dangling link set the new one active
		makeactive=true
	    fi
	}
	cd ${instroot}

	# remove old version
	$sudocmd rm -rf Director
	$sudocmd tar xf $ingtar director &&
	    $sudocmd tar xf director/install.pgz &&
	    $sudocmd rm -r director ||
	{
	    cat << EOF
An error occurred while installing Actian Director.

EOF
	    return 1
	}

	new_install=1

	# correct ownership
	$sudocmd chown -R $ingusr $instroot/Director

	# install under /usr/bin/ with alternatives
	$sudocmd $alternatives --install \
	    /usr/bin/director director \
	    ${instroot}/Director/director 1

	# set new install active as needed
	$makeactive && $sudocmd $alternatives --set \
	    director ${instroot}/Director/director

        cat << EOF
Director successfully installed under:

    ${instroot}/Director

EOF
    else
	return 1
    fi

    if [ -f "${instroot}/Director/jre/legal.tar.gz" ] ; then
        (cd ${instroot}/Director/jre; rm -rf legal; tar -zxf legal.tar.gz; rm -f legal.tar.gz; )
    fi

	# Copy TPN from saveset into installation directory
	if [ $new_install -eq 1 ] ; then
	    adexe=`readlink -f /usr/bin/director 2> /dev/null`
	    if [ -x "$adexe" -a -f ${dir_tpnfile} ] ; then
	        addir=`dirname $adexe`
	        instroot=`dirname $addir`
	        cp ${dir_tpnfile} ${instroot}/Director/THIRDPARTYNOTICES.TXT ||
	            echo "WARNING: Error copying THIRDPARTYNOTICES.DIRECTOR file into place."
	    fi
	fi

	return 0
}

# Check if firewall is running and warn if it is
check_firewall()
{
    firewall_up=false
    if [ -x /sbin/iptables ] ; then
	iptables=/sbin/iptables
    elif [ -x /usr/sbin/iptables ] ; then
	iptables=/usr/sbin/iptables
    else
	cat << EOF
WARNING:
Cannot locate 'iptables' skipping firewall check...

EOF
	return 0
    fi

    if `$sudocmd $iptables -n -L 2>/dev/null | grep "^Chain INPUT" | grep -q "ACCEPT"` ; then
	firewall_up=true
	# INPUT policy is to accept connections
	# check for rules
	if [ `$sudocmd $iptables -n -L INPUT 2>/dev/null | wc -l` -le 2 ] ; then
	    firewall_up=false
	fi
    fi

    $firewall_up && cat << EOF
WARNING:

A firewall appears to be running, this may prevent users
from connecting remotely.

EOF

    return 0
}

#
# do_postinst() - misc post install processing
do_postinst()
{
    if $usesudo ; then
	# can't write to ii_system
        logdir=/tmp
    else
        logdir=${instloc?}/ingres/files
    fi
    if [ -f ${instloc}/.ing${inst_id}sh ] ; then
	envfile=${instloc}/.ing${inst_id}sh
    else
	envfile=${instloc}/ingres/.ing${inst_id}sh
    fi
    source $envfile
    id=`id -u`
    prc=0

    if [ ${doinstall?} != "done" ] ; then
	# running as actian/ingres user.
	dnsetup=`iigetres ii.$CONFIG_HOST.config.hdfs.datanodes.$RELEASE_ID`
	$vhinst && [ "$dnsetup" != complete ] &&
	{
	    # Can we access via SSH/RSA
	    ingadmin=`iigetres ii.$CONFIG_HOST.setup.owner.user`
	    leadernode=`iigetres ii.$CONFIG_HOST.x100.hdfs.leadernode`
	    workers_file=$II_SYSTEM/ingres/files/hdfs/workers
	    homedir=`eval echo ~$USER`
            if [ "$homedir" = "~$USER" ] ; then
                homedir=`getent passwd $USER | cut -d: -f6`
            fi
	    knownhosts="$homedir/.ssh/known_hosts"
	    sshok=true

	    # Datanode setup failed, check
	    for host in `cat $workers_file`
	    do
		# add worker to know_hosts file if needed.
		( ssh-keygen -F ${host?} > /dev/null ||
		    ssh-keyscan -H ${host} >> ${knownhosts} ) 2> /dev/null &&
		( # skip leadernode
		 [ "$host" = "$leadernode" ] ||
			ssh -oBatchMode=yes -oConnectTimeout=10 \
			${ingadmin}@${host} exit 0 >> /dev/null 2>&1 ) || sshok=false
	    done

	    $sshok ||
	    {
		cat << EOF
WARNING:
RSA key ssh connection failed to one or more nodes, reverting to
single node configuration. Saving original workers file to:

${workers_file}.full

EOF
		# password-less ssh not OK, revert to singlenode
		mv $workers_file ${workers_file}.full
		echo $leadernode > $workers_file
	    }
	}

	# generate service script
	if [ "${clipkg}" != "true" ] ; then
        if $systemd
        then
            mksystemd || prc=1
        else
            mkrc || prc=1
        fi

	    # install tutorials if needed
	    logfile="2>&1 | tee -a $logdir/demoinstall.log"
	    $nodemo || eval install_demos $logfile 2>&1 || prc=1
	fi

        ## Start up product
	if [ "${exppkg}" != "true" ] ; then
	    # Ensure environment is correct.
	    iimgmtsvr kill > /dev/null 2>&1
	    ingstart
	    prc=$?
	fi
	# $noroot does not call the script again recursively, so need
	# to set doinstall=done so we will run ingbuild -verify at the end.
	$noroot && doinstall=done
    elif [ "${clipkg}" != "true" ] ; then
	drinstlog="2>&1 | tee -a $logdir/drinstall_$$.log"
	adinstlog="2>&1 | tee -a $logdir/adinstall_$$.log"
	config_host=`iipmhost`
	[ -z "${ingusr}" ] && ingusr=`iigetres ii.${config_host}.setup.owner.user`
	[ -z "${inggrp}" ] && inggrp=`iigetres ii.${config_host}.setup.owner.group`

	check_firewall
	$noad || eval install_ad "$II_SYSTEM" $adinstlog || prc=1

	if [ "${nodemo}" != "true" ] && [ -z "`getent passwd $demo_user`" ] ; then
	   # create OS user for churn demo if needed
	   $sudocmd /usr/sbin/useradd -m -c "Actian Demo User" \
	       $demo_user
	fi

	$exppkg &&
	{
	    # fix ownership
	    inggrp=`groups $ingusr | cut -d ' ' -f 3`
	    for f in demos doc html ingres tutorial vortex.rel
	    do
		[ -r "$II_SYSTEM/$f" ] && $sudocmd chown -h ${ingusr}:${inggrp} $II_SYSTEM/$f
	    done

	    # install serivce
        if $systemd
        then
            installsysd=true
            if [ -x /etc/init.d/actian-client${inst_id} ]
            then
                removerc=true
                if [ "x${interactive}" = "xtrue" ]
                then
                    # offer to not remove
                    prompt "Replace existing sysv rc service script with systemd service file?" y
                    if [ $? -eq 0 ]
                    then
                        removerc=true
                    else
                        removerc=false
                        installsysd=false
                    fi
                fi
                if $removerc
                then
                    echo "Removing sysv rc service script."
                    sudo II_SYSTEM=$II_SYSTEM $II_SYSTEM/ingres/utility/mkrc -r || prc=1
                fi
            fi

            if $installsysd
            then
                sudo II_SYSTEM=$II_SYSTEM $II_SYSTEM/ingres/utility/mksystemd -i &&
                    sudo systemctl stop actian-client${inst_id} > /dev/null 2>&1 &&
                    sudo systemctl start actian-client${inst_id} > /dev/null 2>&1 || prc=1
            fi
        else
            sudo II_SYSTEM=$II_SYSTEM $II_SYSTEM/ingres/utility/mkrc -i &&
                sudo service actian-client${inst_id} stop > /dev/null 2>&1 &&
                sudo service actian-client${inst_id} start > /dev/null 2>&1 || prc=1
        fi

	    $nodemo || do_exp_summary
	}
    fi

    # Ensure we are setting the password in all cases except clipkg
    if [ "${doinstall}" = "done" ] && [ "${clipkg}" != "true" ] ; then
        $upgrade || {
            if [ "x${interactive}" = "xtrue" ]
            then
                $rpmpkg && set_dbms_password
            else
                set_dbms_password
            fi
        }
    fi

    return $prc
}

set_dbms_password()
{
    host=`iipmhost`
    dbmsauth=`iigetres "ii.${host}.dbms.*.dbms_authentication"`
    ii_userid=`iigetres ii.${host}.setup.owner.user`
    pwdlog=/tmp/dbmspwd$$
    [ -z "$dbmsauth" ] && return 1
    [ "$dbmsauth" != "ON" ] && return 0


    . $II_SYSTEM/ingres/utility/iishlib || return 1

	cat << !
DBMS authentication has been enabled for this instance of:

    $prod_name

To allow remote access as user:

    '$ii_userid'

a DBMS password must be set.

!

    # Skip if output is redirected to a file
    # or we're not prompting
    [ -t 1 ] && $prompt || return 0

    while true
    do
	echo
	# turn of input echo
	stty -echo
	iiechonn "Please enter a password (not displayed): "
	read dbpwd
	echo
	iiechonn "Please re-enter the password: "
	read dbpwdconf
	echo
	# re-enable input echo
	stty echo
	echo
	if [ "$dbpwd" != "$dbpwdconf" ]
	then
	    echo "Passwords do not match."
	    continue
	elif [ -z "$dbpwd" ]
	then
	    prompt "Empty password entered, quit?" y && break
	else
	    if $usesudo
	    then
	    	$sudocmd "PATH=$PATH" -E $II_SYSTEM/ingres/bin/sql -u$ii_userid iidbdb << EOF > $pwdlog
alter user $ii_userid with password = '$dbpwd';\g
EOF
	    else
	    	sql -u$ii_userid iidbdb << EOF > $pwdlog
alter user $ii_userid with password = '$dbpwd';\g
EOF
	    fi
	    if [ $? != 0 ] ; then
		cat << EOF
An error occurred while setting the password for the '$ii_userid' user.

See:

    $pwdlog

for more info.

EOF
		return 1
	    else
		echo "DBMS password has been set successfully."
		break
	    fi
	fi
    done
    return 0
}

do_exp_summary()
{
    sumtmplt=${instloc}/ingres/files/summary.tmplt
    htmldir=${instloc}/html/
    thishost=`hostname -f`
    pmhost=`iipmhost`
    mode=`iigetres ii.$pmhost.x100.root_type`
    leadernode=`iigetres ii.$pmhost.x100.hdfs.leadernode`
    numnodes=`iigetres ii.$pmhost.x100.hdfs.numnodes`
    if [ "$mode" = "mapr" ] ; then
	clustername=`ingprenv II_HDFSDATA | cut -d/ -f3`
	hdfs_url="maprfs://${clustername}"
	dfnode=$leadernode
        namenode="None (MapR)"
    else
	hdfsport=`iigetres ii.$pmhost.x100.hdfs.port`
	namenode=`iigetres ii.$pmhost.x100.hdfs.namenode`
	hdfs_url="hdfs://${namenode}:${hdfsport}"
	dfnode=$namenode
    fi
    ii_hdfsdata=`ingprenv II_HDFSDATA`
    dfcom_port=${drclport:-47000}
    dfadmin_port=${dradmport:-47100}
    sumout=index.html
    sum_port=58086
    sum_url="http://${thishost}:${sum_port}/"


    # process template
    [ -r "$sumtmplt" ] &&
    mkdir -p ${htmldir} &&
    cat $sumtmplt | sed -e "s,II_SYSTEM,${instloc},g" \
	-e "s,II_INSTALLATION,${inst_id},g" \
	-e "s,NAME_NODE,${namenode},g" \
	-e "s,MASTER_NODE,${leadernode},g" \
	-e "s,NUM_NODES,${numnodes},g" \
	-e "s,II_HDFSDATA,${ii_hdfsdata},g" \
	-e "s,HDFS_URL,${hdfs_url},g" \
	-e "s,DF_NODE,${dfnode},g" \
	-e "s,DF_ADMIN_PORT,${dfadmin_port},g" \
	-e "s,DF_COM_PORT,${dfcom_port},g" \
	-e "s,VERSION,${prod_rel},g" \
	    > ${htmldir}/${sumout}
    rc=$?

    # launch server
    [ $rc = 0 ] &&
    {
	ssscript=/tmp/start_server$$.sh

	chown -R demo ${htmldir}
	# generate startup script
	cat << EOF > $ssscript
#!/bin/bash
. $II_SYSTEM/ingres/.ing${inst_id}sh
. $II_SYSTEM/ingres/files/rcfiles/iiinitdlib
stop_sumsvr
start_sumsvr
exit $?
EOF
	$sudocmd bash $ssscript
        rc=$?
	rm -f $ssscript
    }

    if [ $rc = 0 ] ; then
	cat << EOF
Details of this installation can be found at:

    ${sum_url}

EOF
    else
	cat << EOF
An error occurred generating the installation summary.

EOF
    fi
    return $rc
}


check_and_set_docker_privileges()
{
    # Continue on non-Linux since the errors will anyway be caught in iisuudfc.
    if [ "$unames" != "Linux" ] ; then
        return
    fi

    # Check for presence of docker group if user wants UDF Container Image to be installed
    if $userespfile ; then
        answer=`grep -w II_DOWNLOAD_UDFC_REPO "$respfile" |awk -F "=" '{print $2}'`
        case "$answer" in
            [Yy]|[Yy][Ee][Ss])
                download_udfc=true;
                ;;
        esac
    fi

    if $download_udfc ; then
        getent group docker > /dev/null ||
        {
            cat << EOF
Group 'docker' does not exist.
UDF container image cannot be installed until docker is made available.
EOF
            exit 2
        }

        # add user to docker group
        id -nG $ingusr | grep -qw docker || $sudocmd /usr/sbin/usermod -a -G docker $ingusr ||
        {
            cat << EOF
Error adding user $ingusr to docker group.
UDF container image cannot be installed.
EOF
            exit 2
        }
    fi
}

#
# Linux rpm install routine
#
#  Description:
#       This script performs a default install of all the Ingres
#       RPMs in the current working directory. The default installation
#	ID will be II unless another is specified.
#
#    Exit Status:
#       3       ingres-LICENSE not run
#       4       Cannot locate core RPM
#	6	Ingres already installed.
#	7	Failed to start ingres
#
install_rpm()
{
    upgrade=false
    upgradeall=false
    needlic=true
    RPMVERS=1.5.0
    RPMPATCHNO=''
    if [ "$RPMPATCHNO" ] ; then
    	RPMBLD=167.${RPMPATCHNO}
    else
    	RPMBLD=167
    fi
    BASEPKG="${pkg_name}"
    COREPKG="${BASEPKG}-${RPMVERS}-${RPMBLD}"
    RPMARCH=`rpm -qp --qf "%{arch}\n" ${rootdir}/rpm/${COREPKG}.*.rpm`
    [ "$RPMARCH" ] ||
    {
	echo "Failed to determine RPM architecture."
	echo "Aborting..."
	exit 1
    }

    #make sure 32bit libraries are present
    #check_libc32

# Use values from response file if we have one
if $userespfile ; then
    II_RESPONSE_FILE=$respfile
    export II_RESPONSE_FILE
    grep '^II_SYSTEM' $respfile > /dev/null &&
    {
	eval `grep '^II_SYSTEM' $respfile`
	export II_SYSTEM
	instloc=$II_SYSTEM
    }
    grep '^II_INSTALLATION' $respfile > /dev/null &&
    {
	eval `grep '^II_INSTALLATION' $respfile`
	export II_INSTALLATION
	inst_id=$II_INSTALLATION
    }
fi

    cat << EOF
Checking for current installations...

EOF
    if [ "${clipkg}" != "true" ] ; then
	# check for old packages
	for oldpkg in ingresvw vectorwise
	do
	    instcore=`rpm -q ${oldpkg} --qf "%{NAME}"`
	    [ $? = 0 ] || instcore=''
	done

	[ -z "$instcore" ] &&
	{
	    instcore=`rpm -q ${BASEPKG} --qf "%{NAME}"`
	    [ $? = 0 ] || instcore=''
	}

	# We can't handle upgrade, so if we found previous
	# installs abort
	[ "$instcore" ] &&
	{
	    pkglist="$instcore
`rpm -q --whatrequires ${instcore} --qf "    %{NAME}\n"`"

	    if $exppkg ; then
		cat << EOF
$brand_name is already installed,
upgrade is not currently supported.

For further assistance, contact Actian Corporation
as per the product Readme.
EOF
	    exit 6
	    fi
	    inst_prefix=`rpm -q --qf "%{INSTPREFIXES}" $instcore`
	    if [ -z "$instloc" ] ; then
		instloc="$inst_prefix"
	    elif ! [ "$instloc" -ef "$inst_prefix" ] ; then
		cat << EOF
$brand_name is already installed under:

    $inst_prefix

It cannot be moved to:

    $instloc

EOF
		exit 6
	    fi

	    # check we can proceed if this is an upgrade
	    II_SYSTEM=$instloc $rootdir/bin/allow_upgrade || exit 6

	    upgrade=true
	}
    fi

    # check for ingbuild install too.
    [ -x "$instloc/ingres/utility/csreport" ] &&
    {
	rc=0
	upgrade=true

	II_SYSTEM=$instloc $instloc/ingres/utility/csreport > /dev/null 2>&1 && rc=8
	if ${clipkg} ; then
	    II_SYSTEM=$instloc
	    PATH=$II_SYSTEM/ingres/bin:$II_SYSTEM/ingres/utility:$PATH
	    if [ "$unames" = "Darwin" ]; then
		DYLD_LIBRARY_PATH=/lib:/usr/lib:$II_SYSTEM/ingres/lib:$DYLD_LIBRARY_PATH
	    else
		LD_LIBRARY_PATH=/lib:/usr/lib:$II_SYSTEM/ingres/lib:$LD_LIBRARY_PATH
	    fi
	    $instloc/ingres/utility/ingstatus | grep running > /dev/null 2>&1
	    # something is running so abort
	    [ $? = 0 ] && rc=8
	fi
	if [ $rc = 8 ]
	then
	    echo "The $brand_name installation under $instloc is running."
	    echo "Aborting installation..."
	    exit $rc
	fi
    }

    $upgrade &&
    {
	II_SYSTEM=$instloc $rootdir/bin/allow_upgrade || exit 6
	cat << EOF
The $brand_name instance under:

    $instloc

will be upgraded.

EOF
    }

    check_and_set_docker_privileges

    ## Do the install
    cat << EOF
II_SYSTEM: $instloc
II_INSTALLATION: $II_INSTALLATION

EOF

# do some delayed checking of the licdir flag
# only applies to Ingres and Vector
    if [ -e ${rootdir}/bin/cilicchk ] && [ "$prod_name" = "Actian Ingres" -o "$prod_name" = "Actian Vector" ] && [ "$express" = "true" ]
    then

        # for a new install check a licdir or respfile was given
        if [ "$upgrade" = "false" ]
        then

            # report error for Ingres rpm express install if -licdir is missing
            # and -respfile not set either

            [ "$userespfile" = "true" ] || [ "$uselicdir" = "true" ] ||
            {
                cat << EOF
Error: The -licdir flag must be supplied for express install if
       a response file is not supplied.

EOF
                usage
                exit 10
            }

        else  # upgrade = true

            # this is an upgrade, which will use the existing license_dir setting
            # warn the user
            if [ "$uselicdir" = "true" ]
            then
                curr_licdir=""
                II_SYSTEM=$instloc
                CONFIG_HOST=`$II_SYSTEM/ingres/utility/iipmhost`
                if [ -n "$CONFIG_HOST" ]
                then
                    curr_licdir=`$II_SYSTEM/ingres/utility/iigetres ii.$CONFIG_HOST.config.license_dir`
                fi

                if [ -n "$curr_licdir" ]
                then
                    if [ "$prompt" = "true" ]
                    then
                        cat << EOF
Warning: This is an upgrade of an existing installation, the -licdir flag
         will be ignored and the existing license directory ($curr_licdir)
         will be used instead.
EOF
                    else
                        cat << EOF
Error: This is an upgrade of an existing installation, the -licdir flag
       should not be specified.
EOF
                        exit 10
                    fi
                fi
            fi
        fi
    fi

    $prompt &&
    {
	while true
	do
        printf "Do you wish to continue? (y/n) [y]: "
        read ans
	    case "$ans" in
		""| \
		[Yy]| \
		[Yy][Ee][Ss])
		    break
		    ;;
		[Nn]| \
		[Nn][Oo])
		    exit 0
		    ;;
		*)
		    continue
		    ;;
	    esac
	done
    }

    CORERPM="${rootdir}/rpm/${COREPKG}.${RPMARCH}.rpm"
    INGLICRPM=`rpm -qp --requires ${CORERPM} | grep ${BASEPKG}-license | \
		cut -d' ' -f1`

    cat << EOF
Checking licensing requirements...

EOF


    ## Check LICENSE has been accepted
    $licaccept && needlic=false

    $needlic &&
    {
	cat << EOF
The License for:

$brand_name $prod_rel

must be read and accepted before installation can proceed.

EOF
	sleep 1
	${rootdir}/bin/ingres-LICENSE || exit 3
    }

    # Validate and use response file if we have one
    if $userespfile ; then
	$quietresp || echo "Using response file: $respfile"
	II_RESPONSE_FILE=$respfile
	export II_RESPONSE_FILE
	grep -q ^II_INSTALLATION $respfile &&
	    eval export `grep ^II_INSTALLATION $respfile` &&
	    inst_id=$II_INSTALLATION && export inst_id
	grep -q ^II_SYSTEM $respfile &&
	    eval export `grep ^II_SYSTEM $respfile` &&
	    instloc=$II_SYSTEM && export instloc
	val=`grep ^II_UPGRADE_USER_DBS $respfile | cut -d= -f2`
	[ "$val" ] &&
	{
 	    case "$val" in
	    [Yy][Ee][Ss]|\
	    [Tt][Rr][Uu][Ee])
	        upgradeall=true
		;;
	    esac
	}

        $actianlic &&
        {
            licdircheck=`grep ^II_LICENSE_DIR $respfile | cut -d= -f2`

            if [ -z "$licdircheck" ]
            then
                echo "II_LICENSE_DIR must be specified in response file."
                exit 1
            fi
        }
    fi

    cat << EOF
Building package list...

EOF
    ## Locate core RPM, if we can't find it, abort
    rpm -q ${COREPKG} > /dev/null 2>&1
    if [ $? != 0 ] ; then
	[ ! -f "$CORERPM" ] && {
	    cat << EOF
Cannot locate the $prod_name ${RPMVERS}.${RPMBLD} core package:

	$CORERPM

EOF
	    usage
	    exit 4
	}
	FILELST=$CORERPM
    fi

    ## Generate install list
    if [ "$RPMARCH" = "x86_64" ] ; then
	PKGLST=$PKGLST64
        if $no32bit ; then
            PKGLST=`echo $PKGLST64 | sed  's/32bit//g'`
        fi
    else
	PKGLST=$PKGLST32
    fi
    for pkg in $PKGLST
    do
	[ -f "${rootdir}/rpm/${BASEPKG}-${pkg}-${RPMVERS}-${RPMBLD}.${RPMARCH}.rpm" ] &&
	{
	    FILELST="$FILELST ${rootdir}/rpm/${BASEPKG}-${pkg}-${RPMVERS}-${RPMBLD}.${RPMARCH}.rpm"
	}
    done

    cat << EOF
Invoking RPM...

EOF

    $actianlic &&
    {
        if [ `echo $FILELST | grep -c dbms` -ne 0 ]
        then
            # tells RPM preinstall script to check license dir before
            # installing
            II_LICDIRCHK_NEEDED=true
            II_LICDIRCHK_FAIL=/tmp/actianlicchk.$$
            II_LICDIRCHK_CILIC=${rootdir}/bin/cilicchk
            export II_LICDIRCHK_NEEDED
            export II_LICDIRCHK_FAIL
            export II_LICDIRCHK_CILIC

            # prompt for licdir in interactive mode
            $interactive &&
            {
                if [ -z "$licdir" ]
                then
                    echo "A license is required for this installation."
                    printf "Enter the directory containing license.xml file : "
                    read licdir
                fi
            }

            if [ "$userespfile" = "false" -a "$upgrade" = "false" ]
            then
                if [ -z "$licdir" ]
                then
                    echo "A directory containing an valid license is required."
                    exit 1
                fi

                licdircheck=$licdir
            fi

            if [ ! -d $licdircheck ]
            then
                echo "$licdircheck does not exist or is not a directory."
                exit 1
            fi
            ${rootdir}/bin/cilicchk -Q -s $licdircheck
            if [ $? -ne 0 ]
            then
                echo "$licdircheck does not contain a valid license."
                exit 1
            fi
        fi
    }

    # if licdir is specified add it in a temporary response file
    # licdir and response file parameters are mutually exclusive
    # hence the need to create a response file just for the license

    licrespfile=/tmp/response.$$.txt
    [ -f $licrespfile ] && rm -f $licrespfile
    if [ "x$licdir" != "x" ] ; then
        respfile=$licrespfile
        II_RESPONSE_FILE=$respfile
        export II_RESPONSE_FILE
        echo II_LICENSE_DIR=$licdir > $respfile
    fi

    # if sparkdownload parameter is specified add it in a temporary response
    # file sparkdownload and response file parameters are mutually exclusive
    # hence need to create a response file for sparkdownload
    if [ \
        "$download_spark" = "true" -o "$download_hadoop" = "true" -o \
        "$download_gcsc" = "true" -o "$download_udfc" = "true" -o \
        "$download_tensorflow" = "true" \
    ] ; then
	if [ "x$licdir" = "x" ] ; then
		respfile=$licrespfile
		II_RESPONSE_FILE=$respfile
		export II_RESPONSE_FILE
	fi
	if $download_spark ; then echo II_DOWNLOAD_SPARK=y >> $respfile ; fi
	if $download_hadoop ; then echo II_DOWNLOAD_HADOOP=Y >> $respfile ; fi
	if $download_gcsc ; then echo II_DOWNLOAD_GCS_CONNECTOR=Y >> $respfile ; fi
	if $download_udfc ; then echo II_DOWNLOAD_UDFC_REPO=Y >> $respfile ; fi
        if $download_tensorflow ; then echo II_DOWNLOAD_TENSORFLOW=Y >> $respfile ; fi
    fi



    # set authstring if present
    $doauthcheck && II_AUTH_STRING="`cat ${authstfile}`" && export II_AUTH_STRING
    rpmcmd="rpm -Uvh"
    $upgrade && rpmcmd="${rpmcmd} --nopostun"
    if [ "$instloc" ] ; then
	$rpmcmd ${allow_unauth} --prefix "$instloc" $FILELST
    else
	$rpmcmd ${allow_unauth} $FILELST
    fi
    rc=$?

    if [ -n "$II_LICDIRCHK_FAIL" ]
    then
        rm -f $II_LICDIRCHK_FAIL
    fi

    if [ $rc = 0 ] ; then

        ## Start up Ingres

        if [ -z "$respfile" ]
        then
            respflag=""
        else
            respflag="-r $respfile"
        fi
        mgmt_svcname=iimgmtsvc
        # we don't have mgmt in client runtime package
        $clipkg && mgmt_svcname=none
        for svc in actian-client $mgmt_svcname
        do
            [ "${svc}" = "none" ] && continue
            if $systemd
            then
                sysdsvc=$svc
                if [ "$sysdsvc" = "actian-client" ]
                then
                    sysdsvc=rdbms
                fi
                if [ -f $sysd_system/${svc}${inst_id}.service ]
                then
                    $instloc/ingres/utility/iisystemd -a configure -d $instloc $respflag -s ${sysdsvc} 
                    rc=$?
                    if [ $rc != 0 ] ; then
                        cat << EOF
An error occurred whilst configuring $prod_name.
The configuration can be re-run using:

    $instloc/ingres/utility/iisystemd -a configure -d $instloc $respflag -s ${sysdsvc}

once the issue has been resolved.

For more information, contact Actian Corporation Technical Support.

EOF
                        exit 7
                    fi
                    systemctl start ${svc}${inst_id}
                    if [ $? -ne 0 ]
                    then
                        exit 7
                    fi
                fi
            else
                if [ -x /etc/init.d/${svc}${inst_id} ] ; then
                    /etc/init.d/${svc}${inst_id} configure $respfile
                    rc=$?
                    if [ $rc != 0 ] ; then
                        cat << EOF
An error occurred whilst configuring $prod_name.
The configuration can be re-run using:

    /etc/init.d/${svc}${inst_id} configure $respfile

once the issue has been resolved.

For more information, contact Actian Corporation Technical Support.

EOF
                        exit 7
                    fi
                    /etc/init.d/${svc}${inst_id} start || exit 7
                else
                    cat << EOF
Error:
Cannot locate service script:

    /etc/init.d/${svc}${inst_id}

EOF
                fi
            fi
        done
    else
        cat << EOF

An error has occurred during the installation of:

$brand_name $prod_rel

EOF
        exit 5
    fi

    ## Copy LICENSE file (legal license text)
    [ $rc -eq 0 ] && cp_lic

    if [ "x$licdir" != "x" ] ; then
        [ -f $licrespfile ] && rm -f $licrespfile
    fi

    # That's it for client installs
    $clipkg &&
    {
	## remove apt config file
	[ -f ${repocfgfile} ] && rm -f ${repocfgfile}
	export doinstall=done
	return
    }

    # Ensure environment is correct.
    source $instloc/.ing${inst_id}sh

    ## Check iimgmtsvr setup
    [ -x "$II_SYSTEM/ingres/bin/iimgmtsvr" ] &&
    {
	II_MTS_JAVA_HOME="`$II_SYSTEM/ingres/bin/ingprenv II_MTS_JAVA_HOME`"
	if [ -z "$II_MTS_JAVA_HOME" ] ; then
	    cat << EOF

WARNING: No Java Runtime Environment (JRE) was detected for
the $prod_name Management Server process. To configure a
JRE to be used by this instance, run:

	$II_SYSTEM/ingres/utility/iisumgmtsvc

For more information, contact Actian Corporation Technical Support.

EOF
	fi
    }

# Install doc separately if it's there
    [ -f "${rootdir}/rpm/${pkg_name}-documentation-${RPMVERS}-${RPMBLD}.${RPMARCH}.rpm" ] &&
    {
	cat << EOF
Installing documentation...

EOF
	rpm -ivh "${rootdir}/rpm/${pkg_name}-documentation-${RPMVERS}-${RPMBLD}.${RPMARCH}.rpm"
    }

    # Warn if upgradedb hasn't been run
    if $upgrade && [ "${upgradeall}" != "true" ] ; then
	cat << EOF

NOTE:
Before you can access the existing databases in this Actian Client
instance, they may have to be upgraded to support the new release of
the Actian Client server which you have installed.

The system databases (iidbdb, imadb) have been upgraded as part of
the installation processes. User databases may be upgraded using the
"upgradedb" utility.

EOF
    fi
    doinstall=done
    export doinstall
    return $rc
} # install_rpm

#
# Linux DEB archive install routine
#
#  Description:
#       This script performs a default install of all the Ingres
#       DEB packages contained apt repository
#	ID will be II unless another is specified.
#
#    Exit Status:
#	8	Error querying existing instance
#	9	Error updating APT repo info
#
install_deb()
{
    needlic=true
    DEBVERS=1.5.0
    DEBBLD=167
    DEBARCH=amd64
    pkgname=${pkg_name}
    repocfgdir=/etc/apt/sources.list.d
    repocfgfile=${repocfgdir}/${short_name}_${DEBVERS}-${DEBBLD}_local.list
    repoconf="deb [arch=$DEBARCH] file:${rootdir}/apt stable non-free"
    sysarch=`dpkg-query -W -f='${Architecture}' dpkg`
    upgrade=false
    upgradeall=false
    startonboot=yes

    if $clipkg ; then
      pkglist="${pkgname}"
    elif $exppkg ; then
      pkglist="${pkgname}"
    else
      pkglist="${pkgname} vectorwise ingresvw"
    fi

    # clean up on exit
    trap "rm -f ${repocfgfile}" EXIT INT HUP

    # check packages match system architecture
    [ "$sysarch" = "$DEBARCH" ] ||
    {
	cat << EOF
ERROR:
'$pkgname:$DEBARCH' is not a valid package for this system.
Only '$sysarch' packages can be installed.
Aborting installation...

EOF
	exit 1
    }
    # check for DEB utilities
    for util in dpkg apt-get
    do
	($util --version > /tmp/${util}.$$ 2>&1) ||
 	{
	    cat << EOF
Failed to locate ${util}

EOF
	    cat /tmp/${util}.$$
	    rm /tmp/${util}.$$
	    usage
	    exit 1
         }
    done

    cat << EOF
Checking for instances...

EOF
    for pkg in $pkglist
    do
	[ "$(dpkg-query --list ${pkg} 2> /dev/null | grep ^ii)" ] &&
	{
	    ingprenv=`dpkg-query --listfiles ${pkg} | grep ingprenv`
	    instloc=`echo $ingprenv | sed -e "s:/ingres/bin/ingprenv::g"`
	    instvers=`apt-cache show ${pkg}|grep ^Version|cut -d' ' -f2`
	    # check installed version
	    dpkg --compare-versions ${instvers} lt ${DEBVERS}.${DEBBLD}-1
	    can_upgrade=$?
	    II_SYSTEM=$instloc
	    export II_SYSTEM
	    cat << EOF
Found existing instance at:

    $II_SYSTEM

Attempting upgrade...

EOF
	    # check we can proceed if this is an upgrade
	    II_SYSTEM=$instloc $rootdir/bin/allow_upgrade || exit 6

	    # override II_INSTALLATION
	    II_INSTALLATION=`$ingprenv II_INSTALLATION`
	    [ -z "$II_INSTALLATION" ] &&
	    {
		cat << EOF
Error:
Unable to determine II_INSTALLATION for the existing instance, aborting...

EOF
		exit 8
	    }

            # If II_HOSTNAME is not set in the environment but is
            # set in the symbol.tbl we need to pick up the value
            # before moving forward with the upgrade. If II_HOSTNAME
            # is not set at all it'll stay that way and we will
            # use the hostname as usual.
            if [ -z "$II_HOSTNAME" ] ; then
                II_HOSTNAME=`$ingprenv II_HOSTNAME`
            fi

	    if [ $can_upgrade != 0 ] ; then
		cat << EOF
Error:
${pkg}=${instvers} is installed.
${pkgname}=${DEBVERS}.${DEBBLD}-1 is not a valid upgrade, aborting...

EOF
		exit 6
	    fi
	    break
	}
    done

    check_and_set_docker_privileges

    cat << EOF

II_SYSTEM: $instloc
II_INSTALLATION: $II_INSTALLATION

EOF
    $prompt &&
    {
	while true
	do
        printf "Do you wish to continue? (y/n) [y]: "
        read ans
	    case "$ans" in
		""| \
		[Yy]| \
		[Yy][Ee][Ss])
		    break
		    ;;
		[Nn]| \
		[Nn][Oo])
		    exit 0
		    ;;
		*)
		    continue
		    ;;
	    esac
	done
    }
    ## Check LICENSE has been accepted
    $licaccept && needlic=false

    $needlic &&
    {
	cat << EOF
The License for:

$brand_name $prod_rel

must be read and accepted before installation can proceed.
Invoking ./ingres-LICENSE...

EOF
	sleep 1
	${rootdir}/bin/ingres-LICENSE || exit 3
	echo
    }

    echo "Adding local repository..."
    if [ ! -d ${repocfgdir} ]
    then
	cat << EOF
Cannot locate APT configuration location:

    ${repocfgdir}

Aborting...
EOF
	exit 9
    fi

    echo "Updating cache..."
    # Add saveset location to repository
    echo ${repoconf} > ${repocfgfile}
    APT_INSECURE_FLAG=""
    if ! $signrelease
    then
        # get apt version as a numeric value we're looking for 1.1 or later
        APT_VER=`apt-get --version | grep "^apt" | cut -d" " -f2 | cut -d. -f1,2 | sed 's/\.//g'`
        if [ $APT_VER -ge 11 ]
        then
            APT_INSECURE_FLAG=--allow-insecure-repositories
        fi
    fi
    apt-get -q update $APT_INSECURE_FLAG > /tmp/aptupd.$$ 2>&1

    [ $? != 0 ] &&
    {
	cat  /tmp/aptupd.$$
	cat << EOF
An error occurred updating the APT repository cache, aborting...

EOF
	## remove apt config file
	[ -f ${repocfgfile} ] && rm -f ${repocfgfile}

	exit 9
    }
    rm -f  /tmp/aptupd.$$

    # need to know if START_ON_BOOT is set. As with iicorepostinst
    # II_START_ON_BOOT takes precedence over response file value
    # so set here and indicate we've done so
    if [ -n "$II_START_ON_BOOT" ]
    then
        startonboot=$II_START_ON_BOOT
        sobfromii=true
    else
        sobfromii=false
    fi

# reset the temp response file
    temprespfile=/tmp/response.$$.txt
    [ -f $licrespfile ] && rm -f $temprespfile

    # Use response file if we have one
    if $userespfile ; then
	$quietresp || echo "Using response file: $respfile"
	II_RESPONSE_FILE=$respfile
	export II_RESPONSE_FILE
	grep -q ^II_INSTALLATION $respfile &&
	    eval export `grep ^II_INSTALLATION $respfile`
	val=`grep ^II_UPGRADE_USER_DBS $respfile | cut -d= -f2`
	[ "$val" ] &&
	{
 	    case "$val" in
	    [Yy][Ee][Ss]|\
	    [Tt][Rr][Uu][Ee])
	        upgradeall=true
		;;
	    esac
	}

        if ! $sobfromii
        then
            val=`grep START_ON_BOOT $respfile | grep -v "^#"| cut -d= -f2|sed 's/ //g'`
            [ "$val" ] &&
            {
                case "$val" in
                    [Yy][Ee][Ss])
                        startonboot=yes
                        ;;
                    [Nn][Oo])
                        startonboot=no
                        ;;
                esac
            }
        fi
    fi

    ## Check sigs if its a signed release
    $signrelease || allow_unauth="--yes --allow-unauthenticated"
    pkgs=`apt-cache search --names-only "${pkgname}\$|${pkgname}-" | \
	   awk '{printf "%s ", $1}'` &&


    $actianlic &&
    {
        if [ `echo $pkgs | grep -c dbms` -ne 0 ]
        then
            if $userespfile ; then
                $actianlic &&
                    {
                        licdir=`grep ^II_LICENSE_DIR $respfile | cut -d= -f2`

                        if [ -z "$licdir" ]
                        then
                            echo "II_LICENSE_DIR must be specified in response file."
                            exit 1
                        fi
                    }
            else
                $interactive &&
                {
                    if [ -z "$licdir" ]
                    then
                        echo "A license is required for this installation."
                        printf "Enter the directory containing license.xml file : "
                        read licdir
                    fi
                }

                # if licdir is specified add it in a temporary response file
                # licdir and response file parameters are mutually exclusive
                # hence the need to create a response file just for the license
                if [ "x$licdir" != "x" ] ; then
                    respfile=$temprespfile
                    II_RESPONSE_FILE=$respfile
                    export II_RESPONSE_FILE
                    echo II_LICENSE_DIR=$licdir > $respfile
                fi
            fi

            if [ -z "$licdir" ]
            then
                echo "A license directory must be specified."
                exit 1
            fi

            if [ ! -d $licdir ]
            then
                echo "$licdir does not exist or is not a directory."
                exit 1
            fi
            ${rootdir}/bin/cilicchk -Q -s $licdir
            if [ $? -ne 0 ]
            then
                echo "$licdir does not contain a valid license."
                exit 1
            fi
        fi
    }


    # check if instance is running
    [ -x "$instloc/ingres/utility/csreport" ] &&
    {
	rc=0
	upgrade=true

	II_SYSTEM=$instloc $instloc/ingres/utility/csreport > /dev/null 2>&1 && rc=8
	if ${clipkg} ; then
	    II_SYSTEM=$instloc \
	    PATH=$II_SYSTEM/ingres/bin:$II_SYSTEM/ingres/utility:$PATH \
	    LD_LIBRARY_PATH=/lib:/usr/lib:$II_SYSTEM/ingres/lib:$LD_LIBRARY_PATH \
	    $instloc/ingres/utility/ingstatus | grep running > /dev/null 2>&1
	    # something is running so abort
	    [ $? = 0 ] && rc=8
	fi
	if [ $rc = 8 ]
	then
	    echo "The $brand_name installation under $instloc is running."
	    echo "Aborting installation..."
	    exit $rc
	fi
    }

    cat << EOF
Invoking apt-get...

EOF

    # set authstring if present
    $doauthcheck && II_AUTH_STRING="`cat ${authstfile}`" && export II_AUTH_STRING


    if [ "$pkgs" ] ; then
	[ -n "${dryrun}" ] && echo "Installing ${pkgs}"
        apt-get install -o Dpkg::Options::="--force-confdef,confmiss" \
	 $pkgs ${dryrun} ${allow_unauth}
       rc=$?
    else
	echo "Empty package list."
	rc=-1
    fi

    # Install license
    [ $rc -eq 0 ] && cp_lic

    # That's in for client installs
    $clipkg &&
    {
	## remove apt config file
	[ -f ${repocfgfile} ] && rm -f ${repocfgfile}
	doinstall=done
	export doinstall
	return
    }

    if [ ! "${dryrun}" ] && [ $rc = 0 ] ; then
    # if sparkdownload parameter is specified add it in a temporary response
    # file sparkdownload and response file parameters are mutually exclusive
    # hence need to create a response file for sparkdownload
    sparkrespfile=/tmp/response.$$.txt
    if [ "$download_spark" = "true" -o "$download_hadoop" = "true" -o "$download_gcsc" = "true" -o "$download_udfc" = "true" -o "$download_tensorflow" = true ] ; then
        respfile=$sparkrespfile
        II_RESPONSE_FILE=$respfile
        export II_RESPONSE_FILE
	if $download_spark ; then echo II_DOWNLOAD_SPARK=y >> $respfile ; fi
	if $download_hadoop ; then echo II_DOWNLOAD_HADOOP=Y >> $respfile ; fi
	if $download_gcsc ; then echo II_DOWNLOAD_GCS_CONNECTOR=Y >> $respfile ; fi
	if $download_udfc ; then echo II_DOWNLOAD_UDFC_REPO=Y >> $respfile ; fi
	if $download_tensorflow ; then echo II_DOWNLOAD_TENSORFLOW=Y >> $respfile ; fi
    fi

	  ## Start up Ingres
    
    if [ -z "$respfile" ]
    then
        respflag=""
    else
        respflag="-r $respfile"
    fi
	for svc in actian-client iimgmtsvc
	do
        if $systemd
        then
            sysdsvc=$svc
            if [ "$sysdsvc" = "actian-client" ]
            then
                sysdsvc=rdbms
            fi
            if [ -f $sysd_system/${svc}${inst_id}.service ]
            then
                $instloc/ingres/utility/iisystemd -a configure -d $instloc $respflag -s ${sysdsvc} 
                rc=$?
                if [ $rc != 0 ] ; then
                    cat << EOF
An error occurred whilst configuring $prod_name.
The configuration can be re-run using:

    $instloc/ingres/utility/iisystemd -a configure -d $instloc $respflag -s ${sysdsvc}

once the issue has been resolved.

For more information, contact Actian Corporation Technical Support.

EOF
                    exit 7
                fi
                systemctl start ${svc}${inst_id}
            fi
        else
            if [ -x /etc/init.d/${svc}${inst_id} ]
            then
                invoke-rc.d ${svc}${inst_id} configure $respfile
                rc=$?
                if [ $rc != 0 ] ; then
                    cat << EOF
An error occurred whilst configuring $prod_name.
The configuration can be re-run using:

    invoke-rc.d ${svc}${inst_id} configure $respfile

once the issue has been resolved.

For more information, contact Actian Corporation Technical Support.

EOF
                    exit 7
                fi
            fi
		fi
        # if START_ON_BOOT is on invoke-rc.d is likely to fail
        # rc = 101 means the start operation was denied
        # in this case we will re-try using 'service'
        if [ "$startonboot" = "yes" ] && ! $systemd
        then
            invoke-rc.d --disclose-deny ${svc}${inst_id} start
            rc=$?
        else
            rc=101
        fi
        if [ $rc -eq 101 ]
        then
            if $systemd
            then
                if [ "$startonboot" = "yes" ]
                then
                    systemctl enable ${svc}${inst_id} > /dev/null 2>&1
                fi
                systemctl start ${svc}${inst_id} > /dev/null 2>&1
            else
                service ${svc}${inst_id} start > /dev/null 2>&1
            fi
            rc=$?
        fi
        if [ $rc -ne 0 ]
        then
            echo "ERROR:failed to start ${svc}${inst_id}"
            exit 7
        fi
	done
    else
	cat << EOF

An error has occurred during the installation of:

$brand_name $prod_rel

EOF
	exit 5
    fi

    # Ensure environment is correct.
    . $instloc/.ing${inst_id}sh
    $upgrade || set_dbms_password

    ## Check iimgmtsvr setup
    [ -x "$II_SYSTEM/ingres/bin/iimgmtsvr" ] &&
    {
	II_MTS_JAVA_HOME="`$II_SYSTEM/ingres/bin/ingprenv II_MTS_JAVA_HOME`"
	if [ -z "$II_MTS_JAVA_HOME" ] ; then
	    cat << EOF

WARNING: No Java Runtime Environment (JRE) was detected for
the $prod_name Management Server process. To configure a
JRE to be used by this instance, run:

	$II_SYSTEM/ingres/utility/iisumgmtsvc

For more information, contact Actian Corporation Technical Support.

EOF
	fi
    }

    # Install director
    $noad ||
    {
	cat << EOF

Installing Director...

EOF
	adpkg=`dpkg-query --list director | grep ^ii | awk '{print $2}'`
	advers=2.4.4.820-1
	instvers=`apt-cache show --no-all-versions ${adpkg} 2> /dev/null |grep ^Version|cut -d' ' -f2 `
	if [ "$instvers" ] ; then
	    # check installed version
	    dpkg --compare-versions ${instvers} lt ${advers}
	    can_install=$?
	else
	    can_install=0
	fi
	if [ $can_install -eq 0 ] ; then
	    apt-get install -o Dpkg::Options::="--force-confdef,confmiss" \
	    director=${advers} ${dryrun} ${allow_unauth}
	else
	    echo "${adpkg}=${instvers} already installed."
	fi
	echo
    }

	# Copy TPN from saveset into installation directory
	if [ -f ${dir_tpnfile} ] ; then
	    adexe=`readlink -f /usr/bin/director 2> /dev/null`
	    if [ -x "$adexe" ] ; then
	        addir=`dirname $adexe`
	        instroot=`dirname $addir`
                cp ${dir_tpnfile} ${instroot}/Director/THIRDPARTYNOTICES.TXT ||
                    echo "WARNING: Error copying THIRDPARTYNOTICES.TXT file into place."
	    fi
	fi

    ## remove apt config file
    [ -f ${repocfgfile} ] && rm -f ${repocfgfile}

    # Warn if upgradedb hasn't been run
    if $upgrade && [ "${upgradeall}" != "true" ] && [ "${clipkg}" != "true" ] ; then
	cat << EOF

NOTE:
Before you can access the existing databases in this Actian Client
instance, they may have to be upgraded to support the new release of
the Actian Client server which you have installed.

The system databases (iidbdb, imadb) have been upgraded as part of
the installation processes. User databases may be upgraded using the
"upgradedb" utility.

EOF
    fi
     return 0
} # install_deb

#
# Unix tar archive install routine
#
#  Description:
#       Performs a default install of the ingres.tar archive
#       in the current working directory. The default installation
#	ID will be II unless another is specified.
#
#    Exit Status:
#       6       Cannot locate tar binary or archive
#	7	$ingusr user doesn't exist
#	8	Cannot create II_SYSTEM
#	9	ingbuild failed
#
install_tar()
{
    if $clipkg ; then
	ingtar=$rootdir/client.tar
    else
	ingtar=$rootdir/${arc_name}.tar
    fi
    export ingtar
    II_DISTRIBUTION=$ingtar
    export II_DISTRIBUTION

    [ -x "/bin/tar" ] && tar=/bin/tar
    [ -z "$tar" ] && tar=`which tar 2>/dev/null`
# Check tar and archive exists
    [ -x "$tar" ] ||
    {
	cat << EOF
Cannot locate tar command. Check path and try again.

EOF
	exit 6
    }

# Use response file if we have one
if $userespfile ; then
    II_RESPONSE_FILE=$respfile
    export II_RESPONSE_FILE
    grep '^II_SYSTEM' $respfile > /dev/null &&
    {
	eval `grep '^II_SYSTEM' $respfile`
	export II_SYSTEM
	instloc=$II_SYSTEM
    }
    grep '^II_INSTALLATION' $respfile > /dev/null &&
    {
	eval `grep '^II_INSTALLATION' $respfile`
	export II_INSTALLATION
	inst_id=$II_INSTALLATION
    }
fi

# First time through just do the setup
if [ "$doinstall" != "true" ] || $noroot
then
    if $userespfile ; then
	$quietresp || echo "Using response file: $respfile"
    fi

    # Ensure 32 bit libraries are available if needed
    # check_libc32
    [ -z "$II_SYSTEM" ] && II_SYSTEM=$instloc
    export II_SYSTEM
    PATH=$II_SYSTEM/ingres/bin:$II_SYSTEM/ingres/utility:$rootdir/bin:$PATH
    export PATH

    # check if instance is owned by RPM or DEBs
    rpmtst=false
    debtst=false
    [ -x /bin/rpm -o -x /usr/bin/rpm ] && rpmtst=true
    [ -x /bin/dpkg -o -x /usr/bin/dpkg ] && debtst=true

    rc=1
    $rpmtst &&
    {
        pkg=`rpm -qf $II_SYSTEM/ingres/bin/iigcn 2> /dev/null`
        rc=$?
    }

    $debtst &&
    {
	pkg=`dpkg -S $II_SYSTEM/ingres/bin/iigcn 2> /dev/null`
        rc=$?
        [ $rc = 0 ] &&
        {
            pkg=`echo $pkg 2> /dev/null | cut -d: -f1`
            rc=$?
        }
    }

    [ $rc -eq 0 ] &&
    {
	cat << EOF
ERROR:
The files under:

    $II_SYSTEM

are managed by the following package:

    $pkg

This package must be removed before the installation can
continue in this location.
Aborting...

EOF
	exit 1
    }

    set_lib_path

    # check for upgrades
    # grab ingusr from config.dat if we can
    [ -x "$II_SYSTEM/ingres/utility/iigetres" ] &&
    {
	host=`iipmhost`
        usr=`iigetres ii.${host}.setup.owner.user`
	[ "$usr" ] && ingusr=$usr
	export ingusr
	upgrade=true
    }

    if [ "$upgrade" = "true" ] ; then

        $rootdir/bin/iiupdateleader || exit 6
    fi

    if [ -f $II_SYSTEM/vortex.rel ] ; then
	# check it's a valid upgrade path
	instver=`grep ^AH $II_SYSTEM/vortex.rel 2>/dev/null | cut -d' ' -f2 `
	[ "$instver" ] || instver=1.0.0
	if [ $prod_rel = $instver ] ; then
	    cat << EOF
$prod_name $prod_rel is already installed.

EOF
	    exit  1
	elif [ $prod_rel = 3.0.0 -a $instver = 2.0.0 ] ; then
	    true
	else
	    cat << EOF
Upgrade is not supported for this release.

EOF
	    exit 1
	fi
    fi

    # do some delayed checking of the licdir flag
    # only applies to Ingres and Vector
    if [ -e ${rootdir}/bin/cilicchk ] && [ "$prod_name" = "Actian Ingres" -o "$prod_name" = "Actian Vector" ] && [ "$express" = "true" ]
    then

        # for a new install check a licdir or respfile was given
        if [ "$upgrade" = "false" ]
        then

            # report error for Ingres rpm express install if -licdir is missing
            # and -respfile not set either

            [ "$userespfile" = "true" ] || [ "$uselicdir" = "true" ] ||
            {
                cat << EOF
Error: The -licdir flag must be supplied for express install if
       a response file is not supplied.

EOF
                usage
                exit 10
            }

        fi
    fi

    # Check $ingusr user exists
    $noroot ||
    {
        if $sucmd "$ingusr" -c "exit 0" > /dev/null 2>&1 ; then
	    [ "$inguid" ] && cat << EOF
WARNING:
UID specified for '$ingusr' but user already exists, ignoring...

EOF
	else
	    cat << EOF
System user "$ingusr" must be created before the installation can proceed.

EOF
	    if $vwinst ; then
		[ -z "$inguid" ] &&
		{
		    # try to pick a uid that won't exist on any nodes.
		    dfltuid=500
		    logindefs=/etc/login.defs
		    if [ -r "${logindefs}" ] ; then
			# sanity check if we can
			dflt=`grep ^SYS_UID_MIN ${logindefs} | awk '{print $2}'`
			# default to 101 if not defined (from man login.defs)
			suid_min=${dflt:-101}
			dflt=`grep ^SYS_UID_MAX ${logindefs} | awk '{print $2}'`
			if [ "$dflt" ] ; then
			    suid_max="$dflt"
			else
			    # no SYS_UID_MAX use UID_MIN-1
			    dflt=`grep ^UID_MIN ${logindefs} | awk '{print $2}'`
			    suid_max=`eval expr $dflt - 1`
			fi
			suid_diff=`eval expr $suid_max - $suid_min`
			if [ $dfltuid -lt $suid_min -o $dfltuid -gt $suid_max ] ; then
			    # pick a value in the middle
			    dfltuid=`eval expr $suid_min + $suid_diff / 2`
			fi
		    fi

		    inguid=$dfltuid
		    # make sure id is unique
		    while ( getent passwd $inguid > /dev/null 2>&1 )
		    do
			inguid=`eval expr $inguid + 10`
		    done
		}

		if [ "$unames" = "Darwin" ]
		then
		    $sudocmd /usr/sbin/sysadminctl -addUser $ingusr -shell /bin/bash \
			-fullName "$brand_name Super User" -UID $inguid
		else
		    $sudocmd /usr/sbin/useradd --system -s /bin/bash -m \
			-c "$brand_name Super User" --uid $inguid $ingusr
		fi
		rc=$?

		$express ||
		{
		    $sudocmd passwd $ingusr
		    rc=$?
		}
		[ $rc != 0 ] && exit 2
	    else
		exit 2
	    fi
	fi
    }

    check_and_set_docker_privileges

    # home dir
    homedir=`eval echo ~$ingusr`
    if [ "$homedir" = "~$ingusr" ] ; then
        homedir=`getent passwd $ingusr | cut -d: -f6`
    fi

    if $noroot ; then
        test -w $homedir
	rc=$?
    else
        $sucmd "$ingusr" -c "test -w $homedir"
	rc=$?
    fi

    [ $rc = 0 ] ||
    {
	cat << EOF
The home directory for the "$ingusr" user:

    $homedir

is not writable.
EOF
	exit 2
    }

    # check saveset it going to be readable as $ingusr
    $noroot || $sucmd $ingusr -c "test -r \"$ingtar\"" ||
    {
	cat << EOF
Unable to read product archive:

    $ingtar

as the $ingusr user. Try extracting:

    `basename ${rootdir}`.tgz

to a globally readable location such as /tmp.

EOF
	exit 6
    }


# Need to make sure II_SYSTEM is readable by user $ingusr. If it isn't we
# abort the install.
    if [ -d "$II_SYSTEM" ] && [ "${noroot}" != "true" ] ; then
	if $sucmd $ingusr -c "sh -c 'test ! -r \"$II_SYSTEM\" ' " ; then
	    rc=7
	    cat << !
Specified location for II_SYSTEM is not readable by user $ingusr.

        II_SYSTEM=$II_SYSTEM

II_SYSTEM must be readable by user $ingusr for the installation to proceed.
!
	    exit $rc
	elif $sucmd $ingusr -c "sh -c 'test ! -x \"$II_SYSTEM\" ' " ; then
	    rc=7
	    cat << !
User $ingusr does NOT have execute permission for the location specified
for II_SYSTEM.

        II_SYSTEM=$II_SYSTEM

User $ingusr must have execute permission in II_SYSTEM for installation
to continue.
!
	    exit $rc
	fi
    fi

# Echo config
    [ "$upgrade" = "false" ] && {
    cat << EOF
$brand_name $prod_rel $name_suffix

will be installed with the following configuration:

II_SYSTEM: $II_SYSTEM
EOF
[ "$II_INSTALLATION" ] && echo "II_INSTALLATION: $II_INSTALLATION"
[ -n "$userflag" ] && echo "Instance Owner: $ingusr"
    }
echo

    $prompt &&
    {
	while true
	do
        printf "Do you wish to continue? (y/n) [y]: "
        read ans
	    case "$ans" in
		""| \
		[Yy]| \
		[Yy][Ee][Ss])
		    break
		    ;;
		[Nn]| \
		[Nn][Oo])
		    exit 0
		    ;;
		*)
		    continue
		    ;;
	    esac
	done
    }

    if $vhinst
    then
	$licaccept ||
	{
	    cat << EOF
The License for:

$brand_name $prod_rel

must be read and accepted before installation can proceed.

EOF
	    sleep 1
	    ${rootdir}/bin/ingres-LICENSE || exit 3
	}

	# need rsync, check we have it
	rsync --version >> /dev/null 2>&1 ||
	{
	    cat << EOF
Cannot locate 'rsync' utility. rsync must be installed on ALL
nodes before the installation can continue.
Aborting...

EOF
	    exit 1
	}

	# need ssh-copy-id, check we have it
	ssh-copy-id  >> /dev/null 2>&1
	[ $? -gt 1 ] &&
	{
	    cat << EOF
Cannot locate 'ssh-copy-id' utility. ssh-copy-id must be
installed on ALL nodes before the installation can continue.
Aborting...

EOF
	    exit 1
	}
    fi

    if $vhinst ; then
	# license accepted, don't prompt again
	licaccept=true
	acclicflag=-acceptlicense
    fi
fi
if [ "$doinstall" != "true" ]
then
    userid=$ingusr
    export userid

    # check we can proceed if this is an upgrade
    II_SYSTEM=$instloc $rootdir/bin/allow_upgrade || exit 10

    # vortex only checks
    $vhinst &&
    {
	[ -x ./bin/hdfs_root_setup ] ||
	{
	    cat << EOF
Cannot locate HDFS setup script, aborting...

EOF
	    exit 1
	}

	if $express ; then
	    ./bin/hdfs_root_setup $ldrnlyflag -batch $usesudoflag "$instloc" $inst_id
	elif $interactive ; then
	    ./bin/hdfs_root_setup $ldrnlyflag $usesudoflag $norootflag "$instloc" $inst_id
	else
	    ./bin/hdfs_root_setup $ldrnlyflag $usesudoflag $norootflag "$instloc" $inst_id
	fi
	rc=$?
	[ $rc -ne 0 ] &&
	{
	    cat << EOF

Installation cannot continue, aborting...

EOF
	    exit 1 # fatal error returned
	}
    }

# Create II_SYSTEM
    II_SYSTEM=$II_SYSTEM
    export II_SYSTEM
    echo "Creating $II_SYSTEM..."
    umask 22
    # On macOS, if creating an installation for a different user,
    # run the mkdir as that user so that user owns all of the
    # intermediate directories created in his/her home directory.
    # Otherwise, the owner will generally be "root" for default sub-dirs
    # "Applications/Actian", though the II_SYSTEM directories below
    # that were OK due to specific "chown"s.  If other than the
    # default location has been specified, then there is no way to
    # know what the final ownership should be, so do the normal
    # "$sudocmd ..." commands.
    if [ "$unames" = "Darwin" ] && [ "$USER" != "$ingusr" ] &&
       [ "$definst" = "$instloc" ] ; then
	su $ingusr -c "mkdir -p $II_SYSTEM/ingres"
    else
	$sudocmd mkdir -p $II_SYSTEM/ingres &&
	$sudocmd chown $ingusr $II_SYSTEM/ingres
    fi
    if [ $? -ne 0 ]
    then
	cat << EOF
Failed to create II_SYSTEM:

	$II_SYSTEM

EOF
	exit 8
    fi

    # II_SYSTEM should be owned by $ingusr for express builds
    $sudocmd chown $ingusr $II_SYSTEM/.

# Call self again, as $ingusr to perform the rest of the installation
    doinstall=true
    posterr=false
    export doinstall instloc ingtar mpiroot posterr II_HOSTNAME
    if $vwinst || $usesudo ; then
	# need sudo for RSA key setup to work
	sudo -u $ingusr ingtar=$ingtar doinstall=$doinstall posterr=$posterr \
		mpiroot=$mpiroot II_HOSTNAME=$II_HOSTNAME II_SYSTEM=$II_SYSTEM \
                $selfdir/$self $acclicflag $self_licdirflag $ldrnlyflag \
                $II_INSTALLATION $instloc $respflag $demoflag $adflag \
		$expressflag $interactiveflag $self_downloadsparkflag \
		$self_downloadhadoopflag $self_downloadgcscflag \
		$self_downloadudfcflag $self_downloadtensorflowflag || exit $?
    elif $force_tar ; then
        su $ingusr -c "$selfdir/$self -tar $interactiveflag $acclicflag $self_licdirflag $ldrnlyflag $II_INSTALLATION $instloc $respflag $no32bit_flag $self_downloadsparkflag $self_downloadhadoopflag $self_downloadgcscflag $self_downloadudfcflag $self_downloadtensorflowflag" || exit $?
    else
        su $ingusr -c "$selfdir/$self $acclicflag $self_licdirflag $ldrnlyflag $II_INSTALLATION $instloc $respflag $no32bit_flag $self_downloadsparkflag $self_downloadhadoopflag $self_downloadgcscflag $self_downloadudfcflag $self_downloadtensorflowflag" || exit $?
    fi
	doinstall=done
    export doinstall

    if [ $clipkg = "false" ] ; then
	authexe=`$II_SYSTEM/ingres/bin/ingprenv II_SHADOW_PWD`
	[ -z "$authexe" ] &&
	{
	    # Build password validation program if we can
	    if [ -f /etc/pam.d/login ] ; then
		# use pam if it's configured
		authmech=pam
		# use same config as login
		[ -f /etc/pam.d/ingres ] ||
		    $sudocmd ln -s /etc/pam.d/login /etc/pam.d/ingres
            elif $usesudo ; then
                if sudo test -f /etc/shadow || sudo test -f /etc/security/passwd || sudo test -f /etc/passwd ; then
                    authmech=pw
                fi
            elif [ -f /etc/shadow -o -f /etc/security/passwd -o -f /etc/passwd ] ; then
                   authmech=pw
	    fi

	    [ "${authmech?}" ] &&
	    {
		mkauthexe=$II_SYSTEM/ingres/bin/mkvalid${authmech}
		authexe=$II_SYSTEM/ingres/bin/ingvalid${authmech}
		authdis=$II_SYSTEM/ingres/files/iipwd/ingvalid${authmech}.dis

		if [ -x $mkauthexe ] ; then
		    if $usesudo ; then
			sudo II_SYSTEM=$II_SYSTEM $mkauthexe
		    else
			$mkauthexe
		    fi
		else
		    if [ ! -x $authexe ] ; then
			# Use the distributed version
			[ -f "$authdis" ] &&
			   $sudocmd cp -f ${authdis} "$authexe"
		    fi

		    # Set II_SHADOW_PWD if we need to
		    sudo -u $ingusr II_SYSTEM=$II_SYSTEM $II_SYSTEM/ingres/bin/ingsetenv II_SHADOW_PWD $authexe
		fi

	    }
	}

	# If $authexe exists then it needs to be owned by root
	# and have SUID set.
	[ -x $authexe ] && {
	    $sudocmd chown root $authexe
	    $sudocmd chmod 4755 $authexe
	}
    fi

    # Copy it to home directory if we can
    [ "$homedir" != "$II_SYSTEM/ingres" ] && \
	$sucmd $ingusr -c "cp -f $II_SYSTEM/ingres/.ing*sh $homedir"

    # re-set inst_id incase it was changed by setup
    inst_id=`$II_SYSTEM/ingres/bin/ingprenv II_INSTALLATION`
    export inst_id

else # doinstall=true
# Setup environment
    II_SYSTEM=$instloc
    export II_SYSTEM
    PATH=$II_SYSTEM/ingres/bin:$II_SYSTEM/ingres/utility:$rootdir/bin:$PATH
    export PATH
    set_lib_path

    $noroot &&
    {
       # not root, II_SYSTEM needs to exist and be writable
       [ -w "$II_SYSTEM/ingres" ] ||
           mkdir -p $II_SYSTEM/ingres 2> /dev/null ||
       {
           cat << EOF
ERROR:
II_SYSTEM must exist and be writable as '$ingusr'
when installing as a user other than 'root'.

EOF
           exit 3
       }

	[ -f ${MAPR_HOME:-/opt/mapr}/bin/maprcli ] &&
	{
	    # check current user has login access to cluster
	    mrperms=`maprcli acl show -type cluster -noheader |
			cut -d] -f1`
	    ## Ordinary shells such as HP/UX's take great exception to
	    ## the [[ == ]] syntax at parse time, even when not actually
	    ## executing the branch!  This is the best I could come up with,
	    ## and it seems to work on a linux bash as best as I can tell.
	    eval_mrperms='! [[ "$mrperms" == *login* ]]'
	    if eval $eval_mrperms ; then
		cat << EOF
ERROR:
The 'actian' user does not have 'login' privilege in MapR ACLs.
Run:

    maprcli acl edit -user ${ingadmin}:login

as a privileged user to add it.

EOF
	        exit 3
	    fi
	}
    }

#check to see if instance is running and abort if it is
    [ -x $II_SYSTEM/ingres/utility/csreport ] &&
    {
	rc=0
	upgrade=true

	csreport >> /dev/null && rc=8
	if ${clipkg} ; then
	    ingstatus | grep running > /dev/null 2>&1
	    # something is running so abort
	    [ $? = 0 ] && rc=8
	fi

    	if [ $rc = 8 ]
    	then
        	echo "The $prod_name $prod_rel installation under $II_SYSTEM is running."
        	echo "Aborting installation..."
        	exit $rc
    	fi
    }

    # Some Linux distributions like Mandriva have TMPDIR set to ~root/tmp
    # which is inaccessible to Ingres administrator userid, so this is set to /tmp
    if [ "$TMPDIR" ]; then
	TMPDIR=/tmp
	export TMPDIR
    fi

    # if sparkdownload parameter is specified add it in a temporary response
    # file sparkdownload and response file parameters are mutually exclusive
    # hence need to create a response file for sparkdownload
    sparkrespfile=/tmp/response.$$.txt
    [ -f $sparkrespfile ] && rm -f $sparkrespfile
    if [ "$download_spark" = "true" -o "$download_hadoop" = "true" -o "$download_gcsc" = "true" -o "$download_udfc" = "true" -o "$download_tensorflow" = true ] ; then
        respfile=$sparkrespfile
        II_RESPONSE_FILE=$respfile
        export II_RESPONSE_FILE
	if $download_spark ; then echo II_DOWNLOAD_SPARK=y >> $respfile ; fi
	if $download_hadoop ; then echo II_DOWNLOAD_HADOOP=Y >> $respfile ; fi
	if $download_gcsc ; then echo II_DOWNLOAD_GCS_CONNECTOR=Y >> $respfile ; fi
	if $download_udfc ; then echo II_DOWNLOAD_UDFC_REPO=Y >> $respfile ; fi
	if $download_tensorflow ; then echo II_DOWNLOAD_TENSORFLOW=Y >> $respfile ; fi
        [ "x$licdir" != "x" ] && echo II_LICENSE_DIR=$licdir >> $respfile
        userespfile=true
    fi

    # Remove old MPI runtime (4.1) if needed
    if [ -x $II_SYSTEM/ingres/impi/intel64/bin/mpirun ] ; then
	$II_SYSTEM/ingres/bin/ingunset I_MPI_ROOT
	rm -rf $II_SYSTEM/ingres/impi
    fi

    # Remove old MPI runtime (7.0) if needed
    if [ -x $II_SYSTEM/ingres/mpi/intel64/bin/mpirun ] ; then
	$II_SYSTEM/ingres/bin/ingunset I_MPI_ROOT
	rm -rf $II_SYSTEM/ingres/mpi/intel64
    fi

    # ensure MPI utilities are in the path for Vector H
    $vhinst && PATH=$II_SYSTEM/ingres/mpi/bin:$PATH && export PATH
# Install the save set
    echo "Beginning installation..."
    cd $II_SYSTEM/ingres >> /dev/null
    $tar xf $ingtar install

    $doauthcheck && II_AUTH_STRING="`cat ${authstfile}`" && export II_AUTH_STRING
    if $no32bit ; then
	no32bit_str="-exclude=supp32"
    else
	no32bit_str=""
    fi
    if $userespfile ; then
        #ingbuild flags -all and -exclude (via no32bit_str) are mutually exclusive
        #Note: Vector does not offer 32bit at all, so is covered in the else branch
        if $no32bit ; then
            install/ingbuild ${acclicflag} -exresponse -file="$respfile" ${no32bit_str}  $ingtar
        else
            install/ingbuild ${acclicflag} -all -exresponse -file="$respfile" $ingtar
        fi
        rc=$?
    elif $interactive ; then
        if $licinst && ! $vwinst ; then
            install/ingbuild -interactive ${ingbuild_licdirflag}
            rc=$?
        else
	    install/ingbuild ${acclicflag} ${ingbuild_licdirflag} -all $ingtar
	    rc=$?
        fi
    elif $vhinst ; then
	# VectorH, license displayed earlier
        install/ingbuild -acceptlicense -express -install=esql,dbms,net,das,odbc,qr_run,qr_tools,c2audit,mgmtsvc,star $ingtar &&
        install/ingbuild ${acclicflag} ${expressflag} -install=x100mpi $ingtar
        rc=$?
    else
	# default for expres_install.sh
 	install/ingbuild ${acclicflag} ${ingbuild_licdirflag} -express ${no32bit_str} $ingtar
	rc=$?
    fi

    # if ingbuild failed, abort
    [ $rc != 0 ] &&
    {
	echo "ERROR: ingbuild returned '$rc', aborting..."
	return $rc
    }
    [ ! -f "$II_SYSTEM/ingres/files/config.dat" ] &&
    {
	echo "$prod_name $prod_rel was not installed."
	return 1
    }
    # if upgrade failed.
    VER_SYS=`head -1 $II_SYSTEM/ingres/version.rel`
    VER_INST=`$II_SYSTEM/ingres/install/ingbuild -version`
    if [ "$VER_SYS" != "$VER_INST" ] ; then
	echo "$prod_name $prod_rel was not installed (or upgrade failed)."
	return 1
    fi

    $interactive && inst_id=`ingprenv II_INSTALLATION`

    # Set II_HOSTNAME so client runtime can run even if machine
    # name changes.
    if $clipkg ; then
	CONFIG_HOST=`iipmhost`
	$II_SYSTEM/ingres/bin/ingsetenv II_HOSTNAME "$CONFIG_HOST"
    fi

    # Generate environment setup scripts
    rm -f $II_SYSTEM/ingres/.ing${inst_id}*sh
    genenv -b -o $II_SYSTEM/ingres/.ing${inst_id}sh
    $vhinst || genenv -c -o $II_SYSTEM/ingres/.ing${inst_id}csh

    # Copy it to home directory if we're not running as root
    $noroot && [ "$homedir" != "$II_SYSTEM/ingres" ] &&
	cp -f $II_SYSTEM/ingres/.ing*sh $homedir

    if $commupkg ; then
	CONFIG_HOST=`iipmhost`
	# Disable autostats for now, workaround for Mantis 8916
	iisetres ii.$CONFIG_HOST.dbms.*.opf_autostats OFF
    fi


    ## Check other setup
    if [ $rc -eq 0 ] ; then
	$vhinst &&
	{
	    # Set MPI_ROOT in the symbol table for Vector HDFS
	    if [ -x $II_SYSTEM/ingres/mpi/bin/mpirun ] ; then
		$II_SYSTEM/ingres/bin/ingsetenv MPI_ROOT "$II_SYSTEM/ingres/mpi"
	    else
		cat << EOF
WARNING: Cannot locate MPI Runtime.

EOF
	    fi
	}

        ## Check for completed installation
	[ -f "$II_SYSTEM/ingres/files/config.dat" ] &&
	{
	    CONFIG_HOST=`iipmhost`
	    VERSION=`head -1 $II_SYSTEM/ingres/version.rel`
	    RELEASE_ID=`echo $VERSION | sed "s/[ ().\/]//g"`
	    if $clipkg ; then
	        SETUP=`iigetres ii.$CONFIG_HOST.config.net.$RELEASE_ID`
	    else
	        SETUP=`iigetres ii.$CONFIG_HOST.config.dbms.$RELEASE_ID`
	    fi

	    $vhinst &&
	    {
	 	dnsetup=false
		# if DBMS setup is OK, check HDFS too
		[ "$SETUP" = "complete" ] &&
		{
		    SETUP=`iigetres ii.$CONFIG_HOST.config.hdfs.leadernode.$RELEASE_ID`
		    dnsetup=`iigetres ii.$CONFIG_HOST.config.hdfs.datanodes.$RELEASE_ID`
		    [ "$SETUP" ] ||
		    {
			cat << EOF
ERROR:
HDFS setup has not been completed for:

    Actian Client $VERSION

See install.log for more info.

EOF
		        rc=5
		    }
		}
	    }

	}

	[ -x "$II_SYSTEM/ingres/bin/iimgmtsvr" ] &&
	{
	    II_MTS_JAVA_HOME="`$II_SYSTEM/ingres/bin/ingprenv II_MTS_JAVA_HOME`"
	    if [ -z "$II_MTS_JAVA_HOME" ] ; then
		cat << EOF

WARNING: No Java Runtime Environment (JRE) was detected for
the $prod_name Management Server process. To configure a
JRE to be used by this instance, run:

	$II_SYSTEM/ingres/utility/iisumgmtsvc

For more information, contact Actian Corporation Technical Support.

EOF
		sleep 2
	    fi
	}

	if $vhinst &&
	   [ "$SETUP" = "complete" -a "$dnsetup" != "complete" ] &&
	   [ "${leaderonly}" != "true" ] && [ "${express}" != "true" ]
	then
	    # run datanode setup when we have datanodes
	    numnodes=`wc -l $II_SYSTEM/ingres/files/hdfs/workers | awk '{print $1}'`
	    if [ "$numnodes" -a $numnodes -gt 1 ] ; then
		iisuhdfs -express datanodes
		dnsetup=`iigetres ii.$CONFIG_HOST.config.hdfs.datanodes.$RELEASE_ID`
	    else
		dnsetup=complete
	    fi

	    # Warn if datanode setup not complete
	    if [ "$dnsetup" != "complete" ] ; then
		cat << EOF

WARNING:
Datanode setup has not been completed for Actian Client HDFS.

    Actian Client $VERSION

will only operate in single node mode until the datanode setup
has been completed. Use:

    iisuhdfs datanodes

to run the datanode setup.

EOF
	    fi
	    if $upgrade ; then
		cat << EOF
NOTE:
Before you can access the existing databases in this Actian Client
instance, they may have to be upgraded to support the new release of
the Actian Client server which you have installed.

The system databases (iidbdb, imadb) have been upgraded as part of
the installation processes. User databases may be upgraded using the
"upgradedb" utility.

EOF
	    fi
	fi

        # Do not return if $noroot
        # $noroot does not call the script again recursively
        # So need to move on to copy license files
        $noroot || return $rc

    fi

fi
rc=$?
[ $rc -eq 0 ] && cp_lic

} # install_tar

#
# install_demos()
#
install_demos()
{
    # check for demos
    [ `ls -1 $rootdir/demos/*.json 2>/dev/null | wc -l` = 0 ] && return 0

    # shutdown management server first
    echo "Installing Demos..."
    rc=0
    iimgmtsvr kill > /dev/null 2>&1
    (
	cd $rootdir
	for pkginfo in $rootdir/demos/*.json
	do
	    $rootdir/bin/pkginst $pkginfo
	    [ $? != 0 ] && rc=1
	done
    )

    return $rc
}


# Get installation location # and ID
get_instconf()
{
    # Installation location
    while [ -z "$instloc" ]
    do
	cat << EOF
Enter the location to install:

    $brand_name $prod_rel

EOF
        printf "[$definst]: "
	read ans
	[ -z "$ans" ] && ans=$definst
	instloc=`echo $ans | grep '^/'`
	echo

	[ "$instloc" ] && validate_path $instloc ||
	{
	    cat << EOF
"$ans" is not a valid installation location.

EOF
	    usage
	    exit 1
        }
    done

    # check for existing install
    [ -x $instloc/ingres/bin/ingprenv ] &&
    {
	II_SYSTEM=$instloc
	export II_SYSTEM
        cat << EOF
An instance of:
    $brand_name
already exists under:
    $II_SYSTEM
This instance will be upgraded.
EOF
	res=`$II_SYSTEM/ingres/bin/ingprenv II_INSTALLATION`
	[ "$res" ] &&
	{
	    inst_id=$res
	    II_INSTALLATION=$inst_id
	}
	if [ "$unames" = "Darwin" ]; then
	    ingusr=`stat -f "%Su" $instloc/ingres/bin/ingprenv`
	elif [ "$unames" = "HP-UX" -o "$unames" = "AIX" -o "$unames" = "SunOS"  ]; then
	    ingusr=`ls -l $instloc/ingres/bin/ingprenv | awk '{ print $3 }'`
	else
	    ingusr=`stat -c "%U" $instloc/ingres/bin/ingprenv`
	fi

        if [ -z "$II_HOSTNAME" ] ; then
            II_HOSTNAME=`$II_SYSTEM/ingres/bin/ingprenv II_HOSTNAME`
        fi
    }

    # Installation ID
    dflt=$inst_id
    while [ -z "$II_INSTALLATION" ]
    do
	cat << EOF
Enter the instance ID to be used for this instance of

    $brand_name $prod_rel

The instance ID is a two character string used to uniquely
identify the instance on this host and to define the listen
address for incoming remote connections. The first character
must be a letter, the second can be a number from 0-9 or
a letter.

EOF
	while true
	do
            printf "[$dflt]: "
	    read ans
	    [ -z "$ans" ] && ans=$dflt
	    case "$ans" in
		[A-Za-z][a-zA-Z0-9])
		    inst_id=$ans
		    II_INSTALLATION=$inst_id
		    echo
		    break
		    ;;
		*)
	    	    cat << EOF
"$ans" is not a valid installation ID.

EOF
		    ;;
	    esac
	done
    done
    export II_INSTALLATION

    # user ID
    if [ -n "$userflag" ] ; then
	if  [ -z "$ingusr" ] ; then
	    if  [ -z "$respuserid" ] ; then
	        ingusr=actian
	        # Installation owner
	        if $interactive ; then
		    cat << EOF
Enter the user to install the product as
EOF
		    printf "[$ingusr]: "
		    read ans
		    [ "$ans" ] && ingusr=$ans
		    echo
                fi
            else
                ingusr=$respuserid
	    fi
	fi
    else
	if  [ -z "$ingusr" ] ; then
	    if  [ -z "$respuserid" ] ; then
                ingusr=actian
            else
                ingusr=$respuserid
	    fi
       fi
    fi

}

#
# Main body of script starts here
#
LANG=C
unames=`uname -s`
unamem=`uname -m`
export unames
[ "$unames" = "Linux" ] && set -o pipefail
self=`basename $0`
selfdir=`dirname $0`
# check for absolute path
if [ "$selfdir" = "." ] ; then
    selfdir=`pwd`
else
    echo $selfdir | grep "^/" >/dev/null
    [ $? = 0 ] || selfdir="`pwd`/$selfdir"
fi

# handle differnt locations
if [ `basename $selfdir` = bin ] ; then
   rootdir=`dirname $selfdir`
else
   rootdir=$selfdir
fi

# strip out trailing '.'
if [ `basename $rootdir` = '.' ] ; then
    rootdir=`dirname $rootdir`
fi

USER=`iiwhoami`
prod_rel=1.5.0
pkg_name=actian-client
arc_name=actian
prod_name="Actian Client"
short_name=Actian
instloc=
PKGLST64='dbms net abf c2audit das esql odbc ome qr_run rep star tuxedo vision spatial 32bit'
PKGLST32='dbms net abf c2audit das esql odbc ome qr_run rep star tuxedo vision spatial'
unset II_SYSTEM II_CONFIG II_ADMIN II_INSTALLATION
rpmpkg=false
debpkg=false
tarpkg=false
clipkg=false
exppkg=false
commupkg=false
vxpkg=false
vhinst=false
vwinst=false
licinst=false
upgrade=false
express=true
interactive=false
express_spec=false
prompt=true
demo_user=demo
noad=false
nodemo=false
no32bit=false
no32bit_flag=""
do_jce=false
actianlic=false
respuserid=""
userspecified=false
type systemctl > /dev/null 2>&1
if [ $? -ne 0 ]
then
    systemd=false
else
    systemd=true

    sysd_system=
    for sys in /usr/lib/systemd/system /lib/systemd/system /etc/systemd/system
    do
        if [ -d "$sys" ]
        then
            sysd_system=$sys
            break
        fi
    done

    if [ -z "$sysd_system" ]
    then
        echo "Aborting due to missing systemd system directory." >&2
        exit 6
    fi
fi
[ "$self" = "client_install.sh" ] && clipkg=true
[ -f "$rootdir/.vortex" ] && vxpkg=true
[ -f "$rootdir/.express" ] && exppkg=true
[ -f "$rootdir/.community" ] && commupkg=true
if $clipkg ; then
    tarfile=client.tar
    noad=true
    nodemo=true
elif [ "$short_name" =  "Ingres" ] ; then
    express=true
    prompt=false
    nodemo=true
    tarfile=${arc_name}.tar
elif $exppkg || $commupkg ; then
    tarfile=${arc_name}.tar
else
    nodemo=true
    demoflag=-nodemo
    tarfile=${arc_name}.tar
fi
name_suffix=""
if [ "" ] ; then
    if $exppkg ; then
	brand_name="Actian Client Express"
    elif $vxpkg ; then
	brand_name=" Vortex"
    else
	brand_name=" $short_name"
    fi
else
    brand_name=${prod_name}
fi
if $commupkg ; then
    name_suffix="Community Edition"
fi
ls $rootdir/rpm/*.rpm > /dev/null 2>&1 && rpmpkg=true
ls $rootdir/apt/ > /dev/null 2>&1 && debpkg=true
ls $rootdir/${tarfile} > /dev/null 2>&1 && tarpkg=true

case "$short_name" in
    Actian)
	    # Actian Client Runtime
	    inst_id=AC
	    vwinst=true
	    express=false
	    do_jce=false
	    actianlic=false
	    ;;
    Vector|\
    Vectorwise)
	    inst_id=VW
	    vwinst=true
            licinst=true
            actianlic=true
	    ;;
    Vector-H|\
    VectorH|\
    Vortex)
	    inst_id=VH
	    vhinst=true
	    do_jce=true
	    vwinst=true
	    express=false
	    ;;
    VectorMPP)
	    inst_id=VM
	    vhinst=true
	    do_jce=true
	    vwinst=true
	    express=false
	    ;;
    "Ingres")
	    inst_id=II
            licinst=true
            actianlic=true
	    [ `uname -s` = "Linux" ] && [ -e $selfdir/readme_a64_lnx.html ] && do_jce=true
	    ;;
    *)
	    echo "Unknown product name: ${short_name}"
	    exit 1
	    ;;
esac

#check if we're reverse hybrid
if $vwinst ; then
    # Vector is never reverse hybrid
    rhybrid=false
elif [ "$unames" = "Linux" ] && [ "$unamem" = "x86_64" ] ; then
    rhybrid=true
elif [ "$unames" = "HP-UX" ] && [ "$unamem" = "ia64" ] ; then
    rhybrid=true
else
    rhybrid=false
fi

# For macOS, use home directory as default location for installation
# rather than a system-wide shared location as on other platforms.
definst_base_contains_homedir=false
if [ "$unames" = "Darwin" ]; then
    definst_base_homedir=~
    definst_base=~/Applications
    definst_base_contains_homedir=true
else
    definst_base=/opt
fi
if $clipkg ; then
    definst="${definst_base}/Actian/${short_name}_Client"
    $debpkg && instloc=$definst
elif $debpkg ; then
    definst="${definst_base}/Actian/${short_name}"
    instloc=$definst
elif $vxpkg ; then
    definst="${definst_base}/Actian/Vortex"
elif $vhinst ; then
    definst="${definst_base}/Actian/Vector${inst_id}"
else
    definst="${definst_base}/Actian/${short_name}${inst_id}"
fi
userespfile=false
uselicdir=false
quietresp=false
respflag=""
ingbuild_licdirflag=""
self_licdirflag=""
self_downloadsparkflag=""
self_downloadhadoopflag=""
self_downloadgcscflag=""
self_downloadudfcflag=""
self_downloadtensorflowflag=""
force_tar=false
licaccept=false
acclicflag=""
expressflag=""
interactiveflag=""
dryrun=""
checksig="${rootdir}/bin/checksig"
allow_unauth=""
signrelease=false
authstfile="${rootdir}/.authstring"
licfile=${rootdir}/LICENSE
tpnfile=${rootdir}/THIRDPARTYNOTICES.TXT
dir_tpnfile=${rootdir}/THIRDPARTYNOTICES.DIRECTOR
reportfile=Attribution-report.html
doauthcheck=true
ldrnlyflag=""
leaderonly=false
noroot=false
norootflag=
usesudo=false
usesudoflag=
sucmd=su
sudocmd=
inguid=
hdinsight=false
download_spark=false
download_hadoop=false
download_gcsc=false
download_udfc=false
download_tensorflow=false
# if .authstring is present and empty disable checking
# otherwise use authstring
if [ -f "${authstfile}" -a ! -s "${authstfile}" ] ; then
    doauthcheck=false
else
    authstfile="${rootdir}/authstring"
fi

if $tarpkg ; then
    if [ "${exppkg}" != "true" -a "${vxpkg}" != "true" ] ; then
	userflag="[-user username] "
	uidflag="[-uid uid] "
	noroot_flag="[-noroot] [-usesudo] "
    fi
    if $exppkg ; then
	demo_flag="[-withdemo|-nodemo]"
    fi
else
    userflag=""
    uidflag=""
    noroot_flag=""
    demo_flag=""
fi
if $vhinst ; then
    leaderonlyflag="[-leaderonly] "
else
    leaderonlyflag=""
fi

# Default to noroot on macOS if no command-line arguments were specified.
# This is considered a more desirable choice on this platform since
# the default install location is in the user's own Applications directory.
if [ "$unames" = "Darwin" ] && [ $# -eq 0 ]; then
    noroot=true
    norootflag=-noroot
    curid=`id  | cut -d'(' -f2 | cut -d')' -f1`
    ingusr=$curid
fi

while [ "$1" ]
do
    case "$1" in
	      -tar)
		    force_tar=true
		    shift
		    [ "$tarpkg" = "" ] &&
		    {
			echo "ingres.tar package not found."
			usage
			exit 9
		    }

		    ;;
	  -respfile)
                    if $uselicdir ; then
                        echo "Error: $1 invalid argument."
                        usage
                        exit 10
                    fi
		    if $download_spark ; then
                        echo "Error: $1 is not permitted with -sparkdownload."
                        usage
                        exit 10
                    fi
		    if $download_hadoop ; then
                        echo "Error: $1 is not permitted with -hadoopdownload."
                        usage
                        exit 10
                    fi
		    if $download_gcsc ; then
                        echo "Error: $1 is not permitted with -gcscdownload."
                        usage
                        exit 10
                    fi
		    if $download_udfc ; then
                        echo "Error: $1 is not permitted with -udfcdownload."
                        usage
                        exit 10
                    fi
		    if $download_tensorflow ; then
                        echo "Error: $1 is not permitted with -tflowdownload."
                        usage
                        exit 10
                    fi
			if $interactive ; then
			echo "Error: $1 invalid argument."
			usage
			exit 10
		    fi
		    if [ ! "$2" ] ; then
			echo "Error: $1 $2 invalid argument."
			usage
			exit 10
		    fi
		    userespfile=true
		    respfile=$2
		    [ -r "$respfile" ] ||
		    {
			echo "Cannot locate response file: $respfile"
			usage
			exit 10
		    }

                    grep -q ^II_USERID $respfile &&
                    {
                        eval `grep '^II_USERID' $respfile`
                        export II_USERID
                        respuserid=$II_USERID

                        if [ "$userspecified" = "true" -a "$ingusr" != "$respuserid" ] ; then
                            echo "Error: -user conflicts with II_USERID in response file."
                            exit 10
                        fi

                        if $noroot
                        then
                            curid=`id  | cut -d'(' -f2 | cut -d')' -f1`
                            if [ "$respuserid" != "$curid" ] 
                            then
                                echo "Error: User cannot be changed with II_USERID if -noroot is specified."
                                exit 10
                            fi
                        fi

                
                    }

	            # II_SPARK_LOCATION and II_DOWNLOAD_SPARK are not valid responsefile parameter for VectorH as
		    # VectorH already have hadoop Spark setup which will be configured by iisuspark
		    if [ "$short_name" = "Vector-H" -o "$short_name" = "VectorH"  -o "$short_name" = "VectorMPP"  -o "$short_name" = "Vortex" -o "$unames" != "Linux" ]; then
			grep II_SPARK_LOCATION "$respfile" > /dev/null
			if [ $? = 0 ]; then
				echo "II_SPARK_LOCATION is not a valid response file parameter."
				usage
				exit 10
			fi
			grep II_DOWNLOAD_SPARK "$respfile" > /dev/null
			if [ $? = 0 ]; then
				echo "II_DOWNLOAD_SPARK is not a valid response file parameter."
				usage
				exit 10
			fi
			grep II_DOWNLOAD_HADOOP "$respfile" > /dev/null
			if [ $? = 0 ]; then
				echo "II_DOWNLOAD_HADOOP is not a valid response file parameter."
				usage
				exit 10
			fi
			grep II_DOWNLOAD_GCS_CONNECTOR "$respfile" > /dev/null
			if [ $? = 0 ]; then
				echo "II_DOWNLOAD_GCS_CONNECTOR is not a valid response file parameter."
				usage
				exit 10
			fi
			grep II_DOWNLOAD_UDFC_REPO "$respfile" > /dev/null
			if [ $? = 0 ]; then
				echo "II_DOWNLOAD_UDFC_REPO is not a valid response file parameter."
				usage
				exit 10
			fi
		    fi

		    # II_SPARK_LOCATION and II_DOWNLOAD_SPARK are mutually exclusive for Vector and AxtianX
		    grep II_SPARK_LOCATION "$respfile" > /dev/null
		    if [ $? = 0 ]; then
			grep II_DOWNLOAD_SPARK "$respfile" > /dev/null
			if [ $? = 0 ]; then
				echo "II_SPARK_LOCATION and II_DOWNLOAD_SPARK in response file $respfile are mutually exclusive."
				usage
				exit 10
			fi
		    fi
		    respflag="$1 $2"
		    shift;shift
		    ;;
		-u|\
	      -user)
		    if $rpmpkg || $debpkg || $exppkg || $vxpkg || $noroot || [ ! "$2" ]
		    then
			echo "Error: $1 $2 invalid argument."
			usage
			exit 10
		    fi
		    # If -user specified, then must change value of default
		    # installation location on systems (eg., macOS) where
		    # the default is based on the home directory.
		    if $definst_base_contains_homedir; then
			homedir_new=`eval echo ~$2`
                        if [ "$homedir_new" = "~$2" ] ; then
                            homedir_new=`getent passwd $2 | cut -d: -f6`
                        fi
			definst=`eval echo $definst | sed -e s,${definst_base_homedir},${homedir_new},`
			definst_base_homedir=$homedir_new
		    fi
		    ingusr=$2
                    userspecified=true

                    if [ "$respuserid" != "" -a "$ingusr" != "$respuserid" ] ; then
                         echo "Error: -user conflicts with II_USERID in response file."
                         exit 10
                    fi
		    shift ; shift
		    ;;
		-i|\
	      -uid)
		    if $rpmpkg || $debpkg || $exppkg || $vxpkg || $noroot || [ ! "$2" ]
		    then
			echo "Error: $1 $2 invalid argument."
			usage
			exit 10
		    fi
		    inguid=$2
		    shift ; shift
		    ;;
	    -noroot)
		    curid=`id  | cut -d'(' -f2 | cut -d')' -f1`
		    if $usesudo || $rpmpkg || $debpkg ||
			[ "$ingusr" ] ; then
			echo "Error: $1 invalid argument."
			usage
			exit 10
		    fi

                    if [ "$respuserid" != "" -a "$respuserid" != "$curid" ]
                    then
                        echo "Error: User cannot be changed with II_USERID if -noroot is specified."
                        exit 10
                    fi

		    noroot=true
		    norootflag=-noroot
		    ingusr=$curid
		    shift
		    ;;
	   -usesudo)
		    type sudo >/dev/null 2>/dev/null
		    if [ $? -ne 0 ]
		    then
			echo "Error: sudo not available on this system."
			usage
			exit 10
		    fi
		    curid=`id  | cut -d'(' -f2 | cut -d')' -f1`
		    if $noroot || $rpmpkg || $debpkg || [ "$curid" = root ]
		    then
			echo "Error: $1 invalid argument."
			usage
			exit 10
		    fi

		    usesudo=true
		    usesudoflag=-usesudo
		    sudocmd=sudo
		    sucmd="sudo su"
		    shift
		    ;;
     -acceptlicense)
                    case "$short_name" in
                        Actian|Ingres)
                            if $interactive ; then
                                echo "Error: $1 is not permitted when -interactive is specified."
                                usage
                                exit 10
                            fi
                            ;;
                        Vector*)
                            ;;
                        *)
                            ;;
                    esac
		    licaccept=true
		    acclicflag=-acceptlicense
		    shift
		    ;;
            -licdir)
                    if $userespfile ; then
                        echo "Error: $1 invalid argument."
                        usage
                        exit 10
                    fi
                    if [ ! "$2" ] ; then
                        echo "Error: $1 $2 invalid argument."
                        usage
                        exit 10
                    fi
		    uselicdir=true
                    licdir=$2
                    [ -r "$licdir/license.xml" ] ||
                    {
                        echo "Cannot locate license file: $licdir/license.xml"
                        usage
                        exit 10
                    }
                    ingbuild_licdirflag="$1=$2"
                    self_licdirflag="$1 $2"
                    shift;shift
                    ;;
     -sparkdownload|-hadoopdownload|-gcscdownload|-udfcdownload|-tflowdownload)
		    if [ "$unames" != "Linux" ]; then
                        echo "Error: $1 invalid parameter."
                        usage
                        exit 10
                    fi
		    if [ "$short_name" = "Vector-H" -o "$short_name" = "VectorH" -o "$short_name" = "VectorMPP" -o "$short_name" = "Vortex" -o "$short_name" = "Actian" ]; then
                        echo "Error: $1 is not supported for $short_name."
                        usage
                        exit 10
                    fi
          	    if $userespfile ; then
			echo "Error: $1 is not permitted when -respfile is specified."
			usage
			exit 10
		    fi
		    if $interactive ; then
		    	echo "Error: $1 is not permitted in interactive mode."
			usage
			exit 10
		    fi
		    [ "$1" = "-sparkdownload" ] && download_spark=true && \
		    self_downloadsparkflag="$1"
		    [ "$1" = "-hadoopdownload" ] && download_hadoop=true && \
		    self_downloadhadoopflag="$1"
		    [ "$1" = "-gcscdownload" ] && download_gcsc=true && \
		    self_downloadgcscflag="$1"
		    [ "$1" = "-udfcdownload" ] && download_udfc=true && \
		    self_downloadudfcflag="$1"
		    [ "$1" = "-tflowdownload" ] && download_tensorflow=true && \
		    self_downloadtensorflowflag="$1"
		    shift
		    ;;
           -express)
		    if $interactive ; then
			echo "Error: $1 invalid argument."
			usage
			exit 10
		    fi
		    express=true
		    licaccept=true
		    express_spec=true
		    expressflag=-express
		    acclicflag=-acceptlicense
		    prompt=false
		    shift
		    ;;
       -interactive)
                    case "$short_name" in
                        Actian|Ingres)
                            if $express_spec || $userespfile || $download_spark || $download_tensorflow \
                            || $download_hadoop || $download_gcsc || $download_udfc || $licaccept ; then
                                echo "Error: $1 invalid argument."
                                usage
                                exit 10
                            fi
                            ;;
                        Vector*)
                            if $express_spec || $userespfile || $download_spark || $download_tensorflow \
                            || $download_hadoop || $download_gcsc || $download_udfc ; then
                                echo "Error: $1 invalid argument."
                                usage
                                exit 10
                            fi
                            ;;
                        *)
                            ;;
                    esac
		    interactive=true
		    express=false
		    licaccept=false
		    interactiveflag=-interactive
		    prompt=true
		    shift
		    ;;
        -leaderonly)
		    leaderonly=true
		    ldrnlyflag=-leaderonly
		    shift
		    ;;
            -dryrun)
		    # don't actually install
		    dryrun=--dry-run
		    shift
		    ;;
	    -withad)
		    if $clipkg
		    then
			echo "Error: $1 invalid argument."
			usage
			exit 10
		    fi
		    # force director install
		    noad=false
		    adflag=$1
		    shift
		    ;;
	      -noad)
		    if $clipkg
		    then
			echo "Error: $1 invalid argument."
			usage
			exit 10
		    fi
		    # no director install
		    noad=true
		    adflag=$1
		    shift
		    ;;
	  -withdemo)
		    if $noroot  || $rpmpkg || $debpkg || $clipkg
		    then
			echo "Error: $1 invalid argument."
			usage
			exit 10
		    fi
		    # force demo install
		    nodemo=false
		    demoflag=$1
		    shift
		    ;;
	    -nodemo)
		    if $noroot  || $rpmpkg || $debpkg || $clipkg
		    then
			echo "Error: $1 invalid argument."
			usage
			exit 10
		    fi
		    # no demo install
		    nodemo=true
		    demoflag=$1
		    shift
		    ;;
	    -no32bit)
                    if [ "${rhybrid}" != "true" -o $interactive = "true" ]
                    then
                        echo "Error: $1 invalid argument."
                        usage
                        exit 10
                    fi
		    no32bit=true
		    no32bit_flag="-no32bit"
		    shift
		    ;;
	[A-Za-z][A-Za-z]|\
	[A-Za-z][0-9])
		    $vxpkg && [ "$1" != "$inst_id" ] &&
		    {
			cat << EOF
The installation ID cannot be changed for:

$brand_name

EOF
			exit 3
		    }
		    definst=`echo $definst | sed -e s,$inst_id,$1,`
		    inst_id=$1
		    II_INSTALLATION=$inst_id
		    export II_INSTALLATION
		    shift
		    ;;
		-d)
		    # legacy flag for passing location
		    # just pass $2 for regular validation
		    shift
		    ;;
		*/*)
		    # Installation location
		    # Check for full path (fixed for express)
		    ( $exppkg || $vxpkg ) && [ "${doinstall}" != "true" ] && [ "$1" != "$definst" ] &&
		    {
			cat << EOF

The installation location cannot be changed for:

$brand_name

EOF
			exit 3
		    }

		    instloc=`echo $1 | grep '^/'`
		    ( [ "${debpkg}" != "true" ] && [ "$instloc" ] && \
			validate_path $instloc ) ||
		    {
			cat << EOF

"$1" is not a valid installation location.

EOF
			usage
			exit 3
		    }
		    shift
		    ;;
		-?|\
		--help|\
		-help)
		    usage
		    exit 0
		    ;;
		 *)
		    cat << EOF
$1 is an invalid installation ID.

EOF
		    usage
		    exit 2
		    ;;
    esac
done

# verify respfile has required parameters
if $userespfile ; then
    $express || $licaccept ||
    {
	echo "-respfile can only be used with either -express or -acceptlicense flag."
	usage
        exit 10
    }
fi
if [ "$download_gcsc" = "true" -a "$download_hadoop" = "false" ] ; then
    if [ "${vhinst}" != "true" -a "$short_name" != "Actian" -a "$unames" = "Linux" ]; then
	echo "-gcscdownload can only be used with -hadoopdownload."
	usage
        exit 10
    fi
fi
if [ -f /etc/hdinsight-motd/motd.txt ] ; then
    hdinsight=true
    # default to sudo for HDInsight and install as current user
    $noroot || {
	usesudo=true
	usesudoflag=-usesudo
	sudocmd=sudo
	sucmd="sudo su"
	ingusr=$USER
	[ -z "$adflag" ] && noad=true
    }
fi


[ "$rpmpkg" = "false" -a "$debpkg" = "false" -a "$tarpkg" = "true" ] && force_tar="true"
if $exppkg || $vxpkg ; then
    scrname="Install"
    if [ "$respuserid" = "" ] ; then
        ingusr=actian
    else
        ingusr=$respuserid
    fi
else
    scrname="Installer"
fi

$interactive ||
{
    II_INSTALLATION=$inst_id
    export II_INSTALLATION
}
# First time round
[ "$doinstall" != "true" ] &&
{
# Startup message
    cat << EOF
$brand_name $prod_rel $scrname

EOF

    # Check user
    if $noroot ; then
	# no root, no extras
	nodemo=true
	noad=true
	if [ "$USER" = "root" ] ; then
	    cat << EOF
$norootflag passed but user is 'root'.

EOF
	    exit 4
	fi
    elif $hdinsight ; then
	if [ "$USER" = "root" ] ; then
	    cat << EOF
Installing as 'root' is not allowed for HDInsight.
Re-run as the ssh login user.

EOF
	    exit 4
	fi
    elif [ "${usesudo}" != "true" ] ; then
	if [ "$USER" != "root" ] ; then
	    cat << EOF
$self must be run as root.

EOF
		exit 4
	fi
    fi


    # verify that, for all DBMS producs (Ingres, Vector*) that use X100, we have libaio available
    if have_x100_server ; then
        [ -f /lib64/libaio.so.1 ] ||
        [ -f /usr/lib64/libaio.so.1 ] ||
        [ -f /lib/x86_64-linux-gnu/libaio.so.1 ] ||
        [ -f /usr/lib/x86_64-linux-gnu/libaio.so.1 ] ||
        [ -f /lib/aarch64-linux-gnu/libaio.so.1 ] ||
        [ -f /usr/lib/aarch64-linux-gnu/libaio.so.1 ] ||
        {
            if [ "$short_name" = "Vector-H" -o "$short_name" = "VectorH" -o "$short_name" = "Vortex" ]; then
                tmp_err_msg=" on ALL nodes"
            else
                tmp_err_msg=""
            fi
            cat << EOF
ERROR:
$brand_name $prod_rel

requires libaio to be installed${tmp_err_msg}. See the
readme.html for information on how to install it.

EOF
            exit 6
        }
    fi


    # verify we have enough resources install Vector/H
    # with default settings
    if $vwinst && [ "${clipkg}" != "true" ]
    then
	if $vhinst ; then
	    minpmemKB=3900000
	    minshmmax=200000000
	else
	    minpmemKB=2000000
	    minshmmax=100000000
	fi

        # physical memory
	pmeminfo=/proc/meminfo
	minpmemMB=`eval expr ${minpmemKB} / 1024`
	if [ -f ${pmeminfo} ]
	then
	    syspmemKB=`cat ${pmeminfo} | grep ^MemTotal | awk '{print $2}'`
	    syspmemMB=`eval expr ${syspmemKB} / 1024`
	    if [ $syspmemKB -lt $minpmemKB ]
	    then
		cat << EOF
ERROR:
$brand_name $prod_rel

requires at least ${minpmemMB}MB of physical memory.
Only ${syspmemMB}MB has been detected.

Aborting installation...
EOF
		rc=10
	        exit $rc
	    fi
	else
	    cat << EOF
WARNING:
Unable to determine the amount of physical memory on this system.
Installation may fail if less than ${minpmemMB}MB is present.

EOF
	    sleep 1
	fi

	# shared memory segments

	shmmaxinfo=/proc/sys/kernel/shmmax
	if [ -r "$shmmaxinfo" ] ; then
	    shmmax=`cat $shmmaxinfo`
	    # check for super large values first, some
	    # large values break test. Any value of 11
	    # characters or more is
	    if [ `echo $shmmax | wc -c` -lt 11 ] &&
	       [ $shmmax -lt $minshmmax ] ; then
		cat << EOF
ERROR:
$brand_name $prod_rel requires a maximum shared memory segment size
greater than $minshmmax but 'kernel.shmmax' is currently set to $shmmax.

Aborting installation...
EOF
		rc=10
	        exit $rc
	    fi
	else
	    cat << EOF
WARNING:
Unable to determine the maximum shared memory segment size
for this system:

    kernel.shmmax

Installation may fail if its less than $minshmmax.

EOF
	    sleep 1
	fi

	if [ "$short_name" = "Vector-H" -o "$short_name" = "VectorH" -o "$short_name" = "Vortex" ]; then
		# check for libatomic too
		[ -f /lib64/libatomic.so.1 ] ||
		    [ -f /usr/lib64/libatomic.so.1 ] ||
		    [ -f /lib/x86_64-linux-gnu/libatomic.so.1 ] ||
		{
		    cat << EOF
ERROR:
$brand_name $prod_rel

requires libatomic to be installed on ALL nodes. See the
readme.html for information on how to install it.

EOF
		    exit 6
		}
	fi
    fi

    # set install config
    if [ "${interactive}" != "true" ] ; then
        [ "$instloc" ] || {
            if $userespfile ; then
                instloc=`grep '^II_SYSTEM' $respfile | cut -d'=' -f2`
            fi
        }
        [ "$instloc" ] || instloc=$definst
    fi

    check_libc32
    get_instconf

    # disk space check
    if $exppkg || $vxpkg ; then
	mindfMB=3000
    elif $clipkg ; then
	mindfMB=300
    else
	mindfMB=1000
    fi

    instdev=${instloc}
    while [ ! -d "${instdev}" ]
    do
       instdev=`dirname ${instdev}`
    done
    if [ "$unames" = "SunOS" ]
    then
    	dfflags="-k"
    else
    	dfflags="-P -k"
    fi
    freeMB=`df ${dfflags} ${instdev} | grep -v '^Filesystem' | awk '{printf "%ld", $4 / 1024}'`
    if [ $mindfMB -gt $freeMB ] ; then
	cat << EOF
ERROR:
$brand_name $prod_rel

requires at least ${mindfMB}MB of free space under:

    ${instloc}

Only ${freeMB}MB is available.

Aborting installation...
EOF
	rc=10
	exit $rc
    fi

    # Check the license if needed. Abort the install if
    # missing the authstring file or it contains a bad key
    if $doauthcheck ; then
	if $commupkg || $exppkg || $vxpkg ; then
	    contact_info="as per the product Readme."
	else
	    contact_info="at eval@actian.com"
	fi
	authok=false
	if [ -f "${authstfile}" ] ; then
	    chmod 666 "${authstfile}"
	    authstring="`cat ${authstfile}`"
	    if ${rootdir}/bin/checkvwkey "$authstring"
	    then
		authok=true
	    else
		cat << EOF
ERROR: Invalid authorization string contained in file:

EOF
	    fi

	else
	    cat << EOF
ERROR: Cannot locate authorization string file:

EOF
	fi
	if [ "${authok}" != "true" ] ; then
	    cat << EOF
    ${authstfile}

A valid authorization string is required to proceed with the installation.
Please contact Actian Corporation $contact_info to obtain one, copy it to
the location above and re-run this script.

EOF
	    exit 9
	fi
    fi

    # for express builds we don't allow upgrade
    instloc20=${definst_base}/Actian/AnalyticsPlatformAH
    if $vxpkg ; then
	# check for AAP
	if [ -f "$instloc20"/vortex.rel ] ||
	   [ -x "$instloc20"/ingres/bin/x100_server ] ; then
	    instver=`grep ^AH $instloc20/vortex.rel 2>/dev/null | cut -d' ' -f2 `
	    [ -z "$instver" ] && instver=2.0.0
	    aploc=$instloc20
	else
	    instver=`grep ^AH $instloc/vortex.rel 2>/dev/null | cut -d' ' -f2 `
	    aploc=$instloc
	fi
	if [ "$instver" ] ; then
	    cat << EOF
Actian Analytics Platform $instver is installed under:

    $aploc

Actian Vortex $prod_rel conflicts with this product and
cannot be installed.

EOF
	    exit 1
	fi

	# check for default Vector H install
	# running instance first
	vhpid=`ps -eaf | grep VH | grep -v Vortex | grep "iigcn\|mgmtsvr" | head -1 | awk '{print $2}'`
	vmpid=`ps -eaf | grep VM | grep -v Vortex | grep "iigcn\|mgmtsvr" | head -1 | awk '{print $2}'`
	if [ "$vhpid" ] ; then
	    # parse process environment for II_SYSTEM
	    for var in `cat /proc/$vhpid/environ | xargs -0`
	    do
		case "$var" in
		    II_SYSTEM*)
			vhloc=`echo $var | cut -d= -f2`
			break
			;;
		esac
	    done
	elif [ "$vmpid" ] ; then
	    # parse process environment for II_SYSTEM
	    for var in `cat /proc/$vmpid/environ | xargs -0`
	    do
		case "$var" in
		    II_SYSTEM*)
			vmloc=`echo $var | cut -d= -f2`
			break
			;;
		esac
	    done
	else
	    # check environment script
	    envscript=`eval echo ~actian/.ingVHsh`
	    if [ -f "$envscript" ] ; then
		vhloc=`grep ^II_SYSTEM ${envscript} | cut -d= -f2`
	    fi
	fi
	[ "$vhloc" ] || vhloc=${definst_base}/Actian/VectorVH
	[ "$vmloc" ] || vmloc=${definst_base}/Actian/VectorVM

	if [ -x ${vhloc}/ingres/bin/x100_server ] ; then
	    instver=`grep ^V $vhloc/ingres/version.rel 2>/dev/null | cut -d' ' -f2 `
	    cat << EOF
Actian Vector $instver is installed under:

    $vhloc

Actian Vortex $prod_rel conflicts with this product and
cannot be installed.

EOF
	    exit 1
	elif [ -x ${vmloc}/ingres/bin/x100_server ] ; then
	    instver=`grep ^V $vmloc/ingres/version.rel 2>/dev/null | cut -d' ' -f2 `
	    cat << EOF
Actian Vector $instver is installed under:

    $vmloc

Actian Vortex $prod_rel conflicts with this product and
cannot be installed.

EOF
	    exit 1
	fi
    elif $exppkg ; then
	instver=`grep ^AH $instloc20/vortex.rel 2>/dev/null | cut -d' ' -f2 `
	[ -z "$instver" ] && instver=2.0.0
	if [ -x "${instloc20}/ingres/bin/x100_server" ] ; then
	   if [ $instver = 2.0.0 ] ; then
	    cat << EOF
Actian Analytics Platform 2.0 is installed under:

    $instloc20

and will be upgraded.

NOTE: Actian DataFlow KNIME installed under:

    ${instloc20}/knime_2.9.4

will be removed as part of the upgrade.

EOF
		while true
		do
        printf "Do you wish to continue? (y/n): "
        read ans
		case "$ans" in
		    [Yy]| \
		    [Yy][Ee][Ss])
			instloc=$instloc20
			upgrade=true
			break
			;;
		    [Nn]| \
		    [Nn][Oo])
			exit 1
			;;
		    *)
			continue
			;;
		esac
		done
		# Create version file if it's missing
		[ -f $instloc/vortex.rel ] || echo "AH 2.0.0 (a64.lnx/00)" > $instloc/vortex.rel

	    else
		instloc=$instloc20
	    fi
	fi
    fi
}
# no user switching without root
$noroot && doinstall=true

# Check for signed archive
[ -x ${checksig} ] &&
{
    signrelease=true
    validate_signature
}

case `uname -s` in
     Linux) reset="- 0"
	    prc=0
	    # tar only an "option" on Linux
	    if $force_tar ; then
		install_tar
		rc=$?
		# Handle any post-install processing here
		[ $rc = 0 ] &&
		{
		    do_postinst
		    prc=$?
		}
	    elif $debpkg ; then
		install_deb
		rc=$?
	    elif $rpmpkg ; then
		install_rpm
		rc=$?
		# Handle any post-install processing here
		[ $rc = 0 ] &&
		{
		    do_postinst
		    prc=$?
		}
	    else
		echo "Error: Unknown archive type..."
		rc=-1
		usage
	    fi


	    # report post install errors but don't abort
	    if [ $rc -ne 0 -o $prc -ne 0 ] ; then
		cat << EOF
An error occurred installing:

$brand_name $prod_rel

Please contact Actian Corporation as per the product
readme for further assistance.

EOF
	    elif [ "$doinstall" != true ] ; then
		cat << EOF
$brand_name $prod_rel

has been successfully installed.

Please refer to the Getting Started section in the Readme file for
the next steps.

EOF
	    fi
	    ;;
        *)  reset=0
	    install_tar
	    ;;
esac

#Display error only when installation is done. Not on every call to this script.
if $force_tar ; then
    if [ "$doinstall" = "done" ] ; then
        if [ "$usesudo" = "true"  ]; then
            sudo -u "$ingusr" II_SYSTEM=$II_SYSTEM "$II_SYSTEM/ingres/install/ingbuild" -verify
        elif [ "$noroot" = "true" ] ; then
            "$II_SYSTEM/ingres/install/ingbuild" -verify
        else
            su $ingusr -c "$II_SYSTEM/ingres/install/ingbuild -verify"
        fi

        install_result=$?

        ## Check for databases which were not upgraded because they are encrypted
        ## and locked, the list is in $II_LOG/upgradedb_locked.log
        ## (provided by upgradedb called in iisudbms)
        upgradelog=$II_SYSTEM/ingres/files/upgradedb_locked.log
        if [ -r $upgradelog ] ; then
            if [ -s $upgradelog ] ; then
                echo
                echo "During the database upgrade locked/encrypted databases were found."
                echo "These databases could not be upgraded automatically."
                echo "Here is the list:"
                echo
                cat $upgradelog
                echo
                echo "You can find the list also in the file"
                echo "    $upgradelog"
                echo
            else
                rm $upgradelog
            fi
        fi

        if [ $install_result = 1 ] ; then
        {
	    cat << EOF
An error occurred installing:

$brand_name $prod_rel

Some packages were not installed or configured correctly.

Please check the install.log and errlog.log for more details.

EOF
        }
        fi
    fi
fi

trap $reset
exit $rc

