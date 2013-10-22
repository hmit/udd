#!/bin/sh

set -e

TARGETDIR=/srv/udd.debian.org/mirrors/blends
WEBCONFGIT=git://git.debian.org/git/blends/website.git
BLENDSWEBDIR=${TARGETDIR}/website
BLENDSWEBCONFSUBDIR=${BLENDSWEBDIR}/webtools/webconf
BLENDSDIR=${TARGETDIR}/blends

mkdir -p $TARGETDIR
cd $TARGETDIR
if [ ! -d ${BLENDSWEBDIR} ] ; then
  git clone ${WEBCONFGIT} >/dev/null 2>/dev/null
else
  if [ ! -d ${BLENDSWEBDIR}/.git ] ; then
    rm -rf ${BLENDSWEBDIR}
    git clone ${WEBCONFGIT} >/dev/null 2>/dev/null
  else
    cd ${BLENDSWEBDIR}
    git stash >/dev/null
    git pull >/dev/null 2>/dev/null
  fi
fi

mkdir -p ${BLENDSDIR}
cd ${BLENDSDIR}
for blend in `ls ${BLENDSWEBCONFSUBDIR} | sed 's/\.conf$//'` ; do
  VcsDir=`grep "^VcsDir" ${BLENDSWEBCONFSUBDIR}/${blend}.conf | sed 's/^VcsDir[:[:space:]]\+//'`
  if [ "" != "$VcsDir" ] ; then
    VcsType=`echo $VcsDir | sed 's/^\([gs][iv][tn]\):.*/\1/'`
    if [ "$VcsDir" = "$VcsType" ] ; then
      if echo $VcsDir | grep -q '^http://.*\.git' ; then
        VcsType=git
      else
        VcsType=""
        echo "$0: Unable to detect VcsType of $VcsDir"
      fi
    fi
    if [ "$VcsType" = "svn" ] ; then
      if [ ! -d $blend ] ; then
        svn checkout $VcsDir >/dev/null 2>/dev/null
      else
        if [ ! -d $blend/.svn ] ; then
          rm -rf $blend
          svn checkout $VcsDir >/dev/null 2>/dev/null
        else
          cd $blend
          svn up >/dev/null 2>/dev/null
          cd ..
        fi
      fi
    fi
    if [ "$VcsType" = "git" ] ; then
      if [ ! -d $blend ] ; then
        git clone $VcsDir $blend >/dev/null && true
        if [ $? -gt 0 ] ; then 
          echo "Unable to fetch initial data for $blend from $VcsDir - try without SSL verification" ;
          GIT_SSL_NO_VERIFY=1 git clone $VcsDir $blend >/dev/null
        fi
      else
        if [ ! -d $blend/.git ] ; then
          rm -rf $blend
          git clone $VcsDir $blend >/dev/null && true
          if [ $? -gt 0 ] ; then
            echo "Unable to create new clone of data for $blend from $VcsDir - try without SSL verification" ;
            GIT_SSL_NO_VERIFY=1 git clone $VcsDir $blend >/dev/null
          fi
        else
          cd $blend
          git stash >/dev/null
          git pull >/dev/null && true
          if [ $? -gt 0 ] ; then
            echo "Unable to pull data for $blend from $VcsDir - try without SSL verification"
            GIT_SSL_NO_VERIFY=1 git pull >/dev/null && true
          fi
          cd ..
        fi
      fi
    fi
  fi
done
