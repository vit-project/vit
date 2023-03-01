import os
import errno

class PidManager:
    """Simple process ID manager.
    """
    def __init__(self, config):
        self.config = config
        self.uid = os.getuid()
        self.pid = os.getpid()
        self._format_pid_dir()
        self._make_pid_filepath()

    def setup(self):
        if self.pid_dir:
            self._create_pid_dir()
            self._write_pid_file()

    def teardown(self):
        if self.pid_dir:
            try:
                os.remove(self.pid_file)
            # TODO: This needs a little more work to skip errors when no PID file
            #       exists.
            #except OSError as e:
            #    if e.errno != errno.ENOENT:
            #        raise OSError("could not remove pid file %s" % self.pid_file)
            except:
                pass

    def _format_pid_dir(self):
        config_pid_dir = self.config.get('vit', 'pid_dir')
        self.pid_dir = config_pid_dir.replace("$UID", str(self.uid))

    def _make_pid_filepath(self):
        self.pid_file = "%s/%s.pid" % (self.pid_dir, self.pid)

    def _create_pid_dir(self):
        try:
            os.makedirs(self.pid_dir, exist_ok=True)
        except OSError:
            raise OSError("could not create pid_dir %s" % self.pid_dir)

    def _write_pid_file(self):
        try:
            with open(self.pid_file, "w") as f:
                f.write(str(self.pid))
        except IOError:
            raise IOError("could not write pid file %s" % self.pid_file)
