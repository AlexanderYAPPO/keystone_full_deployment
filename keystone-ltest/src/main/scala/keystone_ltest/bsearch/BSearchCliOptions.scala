package keystone_ltest.bsearch

import java.io.File

case class BSearchCliOptions(
                            minRps: Int = 10,
                            maxRps: Int = 0,
                            duration: Int = 10, //use int for this and rps so that rps*duration is also an int
                            rounds: Int = 1,
                            userCount: Int = 3,
                            outDir: File = new File("results", s"bsearch-${System.currentTimeMillis()}"),
                            jarPath: File = new File("target/scala-2.11/keystone-ltest-assembly-1.0.jar")
                            )

object BSearchCliOptions {
  val defaults = BSearchCliOptions()
  val parser = new scopt.OptionParser[BSearchCliOptions]("BSearch") {
    override def showUsageOnError: Boolean = true

    opt[Int]("minRps")
      .action((x, o) => o.copy(minRps = x))
      .text(s"min rps (default: ${defaults.minRps})")
    opt[Int]("maxRps")
      .action((x, o) => o.copy(maxRps = x))
      .text(s"max rps (default: ${defaults.maxRps})")
    opt[Int]("duration")
      .action((x, o) => o.copy(duration = x))
      .text(s"single test duration in seconds (default: ${defaults.duration})")
    opt[Int]("rounds")
      .action((x, o) => o.copy(rounds = x))
      .text(s"number of binary search rounds (default: ${defaults.rounds})")
    opt[Int]("userCount")
      .action((x, o) => o.copy(userCount = x))
      .text(s"number of users to create (default: ${defaults.userCount})")
    opt[File]("out-dir")
      .action((x, o) => o.copy(outDir = x))
      .text(s"output dir (default: ${defaults.outDir})")

    help("help").text("prints this usage text")
  }
}
