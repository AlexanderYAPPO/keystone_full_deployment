package keystone_ltest

import java.io.File

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

  log.info("starting simulation")

  val props = new GatlingPropertiesBuilder
  props.simulationClass("keystone_ltest.AuthenticateKeystoneTest")
  props.resultsDirectory(outPath.toString)

  Gatling.fromMap(props.build)

  log.info("simulation done")
  logAppender.stop()
  System.exit(0)
}
