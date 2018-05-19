#   Nido, a Raspberry Pi-based home thermostat.
#
#   Copyright (C) 2016 Alex Marshall
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.
#   If not, see <http://www.gnu.org/licenses/>.

#####

# From "A simple unix/linux daemon in Python" by Sander Marechal
# See http://stackoverflow.com/a/473702/1422096
#
# Modified to add quit() that allows to run some code before closing
# the daemon. See: http://stackoverflow.com/a/40423758/1422096
#
# Joseph Ernest, 2016/11/12
#
# Modified to force instantiator of Daemon class to specify pidfile
# and working directory
#
# Alex Marshall, 2016/12/03

import sys
import os
import time
import atexit
import logging
from signal import signal, SIGTERM


class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run()
    and quit() methods.
    """
    def __init__(self, pidfile, workdir, stdin='/dev/null',
                 stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.workdir = workdir
        self._l = logging.getLogger(__name__)

    def daemonize(self):
        """
        Do the UNIX double-fork magic.

        See Stevens' "Advanced Programming in the UNIX
        Environment" for details (ISBN 0201563177).
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno,
                             e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir(self.workdir)
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno,
                             e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # Register function to call on exit
        atexit.register(self.onstop)
        # Register anonymous function for graceful exit on receiving
        # SIGTERM
        signal(SIGTERM, lambda signum, stack_frame: exit())

        # write pidfile
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("%s\n" % pid)

    def onstop(self):
        self.quit()
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exists. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self._l.info('Starting Nido daemon')
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return None  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon.

        It will be called after the process has been daemonized by
        start() or restart().
        """

    def quit(self):
        """
        You should override this method when you subclass Daemon.

        It will be called before the process is stopped.
        """
