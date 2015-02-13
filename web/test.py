#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import subprocess


def run(cmd):
    ps = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return ps.communicate()[0]


class TestDMD(unittest.TestCase):
    def test_content(self):
        r = run('echo "exit" | ./dmd.cgi')
        self.assertTrue('the accessibility team' in r)

    def test_maintainer_packages(self):
        r = run('./dmd.cgi email1=debian-accessibility@lists.debian.org')
        self.assertTrue('brltty' in r)


class TestBugs(unittest.TestCase):
    def test_content(self):
        r = run('echo "exit" | ./bugs.cgi')
        self.assertTrue('popularity contest' in r)

    def test_bugs_search(self):
        r = run('./bugs.cgi release=sid rc=1')
        self.assertTrue('bugs found' in r)

if __name__ == '__main__':
    unittest.main()
