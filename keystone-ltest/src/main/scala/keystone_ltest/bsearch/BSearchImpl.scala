package keystone_ltest.bsearch

import java.io.{FileFilter, PrintWriter, File}

import org.slf4j.LoggerFactory

class BSearchImpl(opts: BSearchCliOptions) {
  val log = LoggerFactory.getLogger(getClass)

  var runInd = 0
  var round = 0

  val csvResults = new CsvResultsFile(new File(opts.outDir, "res.csv"))
  val resultsFile = new PrintWriter(java.nio.file.Files.newBufferedWriter(new File(opts.outDir, "results").toPath))

  def findSim(testResPath: File) = {
    val files = testResPath.listFiles(new FileFilter {
      override def accept(pathname: File): Boolean = {
        pathname.isDirectory &&
          pathname.getName.startsWith("authenticatekeystonetest-") &&
        new File(pathname, "simulation.log").exists()
      }
    })
    assert(files.length == 1, s"found ${files.length} simulation dirs")

    new File(files(0), "simulation.log")
  }

  def check(testResPath: File, rps: Int): (Boolean, Map[String, String]) = {
    val r = java.nio.file.Files.newBufferedReader(findSim(testResPath).toPath)

    val stats = new RunStats
    var l = r.readLine()
    while (l != null) {
      if (l.startsWith("GROUP")) {
        val parts = l.split('\t')
        //FIXME format from LogFileDataWriter.GroupMessageSerializer depends on Gatling version
        //0 ${GroupRecordHeader.value}$Separator
        //1 $scenario$Separator
        //2 $userId$Separator
        //3 ${serializeGroups(groupHierarchy)}$Separator
        //4 $startTimestamp$Separator
        //5 $endTimestamp$Separator
        //6 $cumulatedResponseTime$Separator
        //7 $status$Eol"
        assert(parts(0) == "GROUP")
        assert(parts(1) == "auth")
        val userId = parts(2).toLong
        assert(parts(3) == "auth")
        val startTs = parts(4).toLong
        val endTs = parts(5).toLong
        val respTime = parts(6).toInt
        assert(endTs - startTs >= respTime , s"unexpected log format ${endTs - startTs} < ${parts(6).toLong}")
        val status = parts(7)

        stats.add(userId, startTs, endTs, respTime, status)
      }
      l = r.readLine()
    }

    stats.check(rps)
  }

  def test(rps: Int): Boolean = {
    runInd += 1
    val testId = f"$runInd%03d-$rps"

    log.info(s"$testId: testing rps=$rps, duration=${opts.duration}s")

    val testResPath = new java.io.File(opts.outDir, testId)
    testResPath.mkdirs

    val w = java.nio.file.Files.newBufferedWriter(new File(opts.outDir, "sc.json").toPath)
    val pw = new PrintWriter(w)
    pw.print(
      s"""{
         |   "Authenticate.keystone":[
         |      {
         |         "runner":{
         |            "rps":${rps},
         |            "type":"rps",
         |            "times":${rps*opts.duration}
         |         },
         |         "context":{
         |            "users":{
         |               "project_domain":"default",
         |               "users_per_tenant":${opts.userCount},
         |               "user_domain":"default",
         |               "tenants":1,
         |               "resource_management_workers":1
         |            }
         |         }
         |      }
         |   ]
         |}
       """.stripMargin)
    pw.close()

    import sys.process._
    val startTm = System.nanoTime()
    val rc = Process(s"java -cp ${opts.jarPath.getAbsolutePath} keystone_ltest.LoadTestRunner $testId", opts.outDir).!
    val simTime = (System.nanoTime() - startTm)/1e9
    log.info(s"simulation took $simTime seconds")

    if (rc != 0) {
      var errFile = new File(testResPath, "err.txt")
      val ex = if (errFile.exists()) {
        val err = scala.io.Source.fromFile(errFile).getLines().take(1).mkString("")
        new Exception(s"simulation failed with rc=$rc, error text: $err")
      } else {
        new Exception(s"simulation failed with rc=$rc")
      }
      log.error("test failed", ex)
      throw ex
    }

    val (passed, rMap) = check(testResPath, rps)

    csvResults.addResult(rMap ++ Map(
      "targetRps" -> rps.toString,
      "simRuntime" -> simTime.toString,
      "simInd" -> runInd.toString,
      "simDuration" -> opts.duration.toString,
      "round" -> round.toString
    ))

    passed
  }

  def bsearch(): Unit = {
    var l = opts.minRps
    var r = opts.maxRps

    while (l > 1 && !test(l)) {
      l /= 2
    }
    if (l < 1) {
      log.error("rps < 1")
      return
    }

    if (r == 0) {
      r = l*2
      while (test(r)) {
        l = r
        r = l * 2
      }
      r -= 1
    }

    while (l < r) {
      val m = (l+r+1) / 2
      if (test(m)) {
        l = m
      } else {
        r = m - 1
      }
    }
    resultsFile.println(l)
    resultsFile.flush()
    log.info(s"max stable rps found: $l")
  }

  def run(): Unit = {
    log.info("starting bsearch")
    while (round < opts.rounds) {
      round += 1
      log.info(s"round $round")
      bsearch()
    }
    csvResults.close()
    resultsFile.close()
  }
}
