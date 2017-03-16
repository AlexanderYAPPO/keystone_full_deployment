package keystone_ltest.bsearch

import java.io.File

import keystone_ltest.LogUtils

object BSearch extends App {
  val opts = BSearchCliOptions.parser.parse(args, BSearchCliOptions.defaults).getOrElse {
    sys.exit(1)
  }

  opts.outDir.mkdirs()

  {
    val appender = LogUtils.addAppender(new File(opts.outDir, "log.txt").toString, true)
    sys.addShutdownHook {
      appender.stop()
    }
    LogUtils.addConsoleAppender()
  }

  new BSearchImpl(opts).run()
}
