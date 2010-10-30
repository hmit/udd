import gatherer
import sources_gatherer
import packages_gatherer


def get_gatherer(connection, config, source):
  return src_and_pkg_gatherer(connection, config, source)

class src_and_pkg_gatherer(gatherer.gatherer):
  def __init__(self, connection, config, source):
    gatherer.gatherer.__init__(self, connection, config, source)
    self.src = sources_gatherer.sources_gatherer(connection, config, source)
    self.pkg = packages_gatherer.packages_gatherer(connection, config, source)

  def run(self):
    if not self.my_config.has_key('no-sources'):
        self.src.run()
    if not self.my_config.has_key('no-binaries'):
        self.pkg.run()
