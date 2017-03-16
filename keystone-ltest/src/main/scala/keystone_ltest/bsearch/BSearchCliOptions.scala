package keystone_ltest.bsearch

import java.io.File

case class BSearchCliOptions(
                            minRps: Int = 10,
                            maxRps: Int = 100,
                            duration: Double = 10,
                            outDir: File = new File("results", s"bsearch-${System.currentTimeMillis()}"),
                            jarPath: File = new File("target/scala-2.11/keystone-ltest-assembly-1.0.jar")
                            )

object BSearchCliOptions {
  val defaults = BSearchCliOptions()
  val parser = new scopt.OptionParser[BSearchCliOptions]("BSearch") {
    override def showUsageOnError: Boolean = true
  }
}
