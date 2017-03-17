package keystone_ltest.bsearch

import java.io.{FileFilter, PrintWriter, File}

import org.slf4j.LoggerFactory

class BSearchImpl(opts: BSearchCliOptions) {
  val log = LoggerFactory.getLogger(getClass)

  var runInd = 0

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

  def check(testResPath: File, rps: Int): Boolean = {
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

    stats.ok(rps)
  }

  def test(rps: Int): Boolean = {
    runInd += 1
    val testId = f"$runInd%03d-$rps"

    log.info(s"$testId: testing rps=$rps")

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
    val rc = Process(s"java -cp ${opts.jarPath.getAbsolutePath} keystone_ltest.LoadTestRunner $testId", opts.outDir).!
    assert(rc == 0)

    check(testResPath, rps)
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

    while (l < r) {
      val m = (l+r+1) / 2
      if (test(m)) {
        l = m
      } else {
        r = m - 1
      }
    }
    log.info(s"max stable rps found: $l")
  }

  def run(): Unit = {
    log.info("starting bsearch")
    bsearch()
  }
}
