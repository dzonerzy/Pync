"""
The MIT License (MIT)
Copyright (c) 2016 Daniele Linguaglossa <d.linguaglossa@mseclab.com>
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import print_function
# This must be the first statement before other statements.
# You may only put a quoted or triple quoted string,
# Python comments, other future statements, or blank lines before the __future__ line.
import __builtin__
import telnetlib
import argparse
import socket
import subprocess
import os

__version__ = "0.1"

parser = argparse.ArgumentParser(description="Python netcat {0} a rewrite of the famous networking tool.".format(__version__))
parser.add_argument("-l", "--listen", default=False, help="listen mode, for inbound connects", action="store_true", dest="listen")
parser.add_argument("-v", "--verbose", default=False, help="verbose (use twice to be more verbose)", action="count", dest="verbosity")
parser.add_argument("-e", "--exec", metavar="", default=False, help="program to exec after connect", dest="program")
parser.add_argument("-s", "--script", metavar="", default=False, help="script to exec after connect", dest="script")
parser.add_argument("-f", "--fork", default=False, help="fork on each connection, must be used with listener", action="store_true", dest="fork")
parser.add_argument("-p", "--local-port", metavar="", help="local port number", dest="local_port", type=int)
parser.add_argument("-V", "--version", default=False, help="output version information and exit", action="store_true", dest="version")
parser.add_argument("host", metavar="HOST",  nargs='?', default=False)
parser.add_argument("port", metavar="PORT",  nargs='?', default=False)
args = parser.parse_args()

def run(args):
    try:
        t = telnetlib.Telnet()
        if args.version:
            __builtin__.print("Python netcat (The GNU Netcat) {0}\n"
                              "Copyright (C) 2017 - 2018  Daniele Linguaglossa\n"
                              "\n"
                              "This program comes with NO WARRANTY, to the extent permitted by law.\n"
                              "You may redistribute copies of this program under the terms of\n"
                              "the GNU General Public License.\n"
                              "For more information about these matters, see the file named COPYING.\n\n"
                              "Original idea and design by Avian Research <hobbit@avian.org>,\n"
                              "Written by Daniele Linguaglossa <danielelinguaglossa@gmail.com>.".format(__version__))

        elif args.local_port and not args.listen:
            raise parser.error("Missing listener switch while using -p")
        elif args.local_port and  args.listen:
            if args.verbosity > 0:
                __builtin__.print("Listening on any port {0}".format(args.local_port))
            t.port=args.local_port
            t.host='0.0.0.0'
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.makefile()
            try:
                s.bind((t.host, t.port))
            except socket.error as e:
                 __builtin__.print("Error: Couldn't bind socket (err={0}): {1}".format(e.args[0], e.args[1]))
            if args.script:
                try:
                    with open(args.script, "r") as script:
                        global print
                        global raw_input
                        print=lambda x: t.write(x)
                        raw_input=lambda: t.read_very_eager()
                        setattr(args, "script_value", script.read())
                        script.close()
                except IOError as e:
                    __builtin__.print("Error: Couldn't execute script (err={0}): {1}".format(e.args[0], e.args[1]))
            s.listen(1)

            def handle_client(args, t, sock, child=False):
                if args.verbosity > 1:
                    __builtin__.print("Connection from {0}:{1}".format(ip[0], ip[1]))
                t.sock = sock
                if args.program:
                    s = t.sock
                    stdin = s.makefile("w")
                    stdout = s.makefile("r")
                    try:
                        p = subprocess.Popen([args.program], stdin=stdin, stdout=stdout, stderr=stdout)
                    except OSError as e:
                        __builtin__.print("Error: Couldn't find executable (err={0}): {1}".format(e.args[0], e.args[1]))
                    p.wait()
                    t.close()
                else:
                    if args.script:
                        exec args.script_value in globals()
                    if not child:
                        t.interact()

            while True:
                sock, ip = s.accept()
                if args.fork:
                    child_pid = os.fork()
                    if child_pid == 0:
                        handle_client(args, t, sock, True)
                        break
                else:
                    handle_client(args, t, sock)
                    break
        elif not args.local_port and not args.host:
            parser.error("Missing argument host")
        elif not args.local_port and not args.port:
            parser.error("Missing argument port")
        elif not args.local_port and args.host and args.port:
            try:
                t.set_debuglevel(args.verbosity)
                if args.script:
                    try:
                        with open(args.script, "r") as script:
                            print=lambda x: t.write(x)
                            raw_input=lambda: t.read_very_eager()
                            setattr(args, "script_value", script.read())
                            script.close()
                    except IOError as e:
                        __builtin__.print("Error: Couldn't execute script (err={0}): {1}".format(e.args[0], e.args[1]))
                t.open(args.host, args.port)
                if args.program:
                    s = t.sock
                    stdin = s.makefile("w")
                    stdout = s.makefile("r")
                    try:
                        subprocess.Popen([args.program], stdin=stdin, stdout=stdout, stderr=stdout)
                    except OSError as e:
                        __builtin__.print("Error: Couldn't find executable (err={0}): {1}".format(e.args[0], e.args[1]))
                if args.script:
                    exec args.script_value in globals()
                t.interact()
            except socket.error as e:
                __builtin__.print("Error: Couldn't create connection (err={0}): {1}".format(e.args[0], e.args[1]))
    except KeyboardInterrupt:
        pass
    except socket.error as e:
        __builtin__.print("Error: Generic error (err={0}): {1}".format(e.args[0], e.args[1]))

run(args)
