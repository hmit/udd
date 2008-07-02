import gatherer
import sources_gatherer
import packages_gatherer


def get_gatherer(connection, config):
  return src_and_pkg_gatherer(connection, config)

class src_and_pkg_gatherer(gatherer.gatherer):
  def __init__(self, connection, config):
    gatherer.gatherer.__init__(self, connection, config)
    self.src = sources_gatherer.sources_gatherer(connection, config)
    self.pkg = packages_gatherer.packages_gatherer(connection, config)

  def run(self, source):
    self.src.run(source)
    self.pkg.run(source)
