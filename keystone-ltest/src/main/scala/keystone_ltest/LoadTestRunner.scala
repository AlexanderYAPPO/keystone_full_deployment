package keystone_ltest

import java.io.{PrintWriter, File}
import java.nio.file.{Paths, Files}

import io.gatling.app.Gatling
import io.gatling.core.config.GatlingPropertiesBuilder
import org.slf4j.LoggerFactory

object LoadTestRunner extends App {
  def usage(): Unit = {
    println("usage: LoadTestRunner <out-path>")
    System.exit(1)
  }
  val log = LoggerFactory.getLogger(this.getClass)

  if (args.length < 1) {
    usage()
  }
  val outPath = new File(args(0))
  if (!outPath.exists || !outPath.isDirectory) {
    usage()
  }

  val logAppender = LogUtils.addAppender(new File(outPath, "log.txt").toString)
  sys.addShutdownHook {
    logAppender.stop()
  }

  log.info("starting simulation")

  val props = new GatlingPropertiesBuilder
  props.simulationClass("keystone_ltest.AuthenticateKeystoneTest")
  props.resultsDirectory(outPath.toString)

  try {
    Gatling.fromMap(props.build)
  } catch {
    case t: Throwable =>
      log.error("simulation failed", t)
      val pw = new PrintWriter(Files.newBufferedWriter(Paths.get(outPath.getPath, "err.txt")))
      t.printStackTrace(pw)
      pw.close()
      System.exit(1)
  }

  log.info("simulation done")
  System.exit(0)
}
