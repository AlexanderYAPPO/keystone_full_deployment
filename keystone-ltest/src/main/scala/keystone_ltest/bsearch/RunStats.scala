package keystone_ltest.bsearch

import org.slf4j.LoggerFactory

import scala.collection.mutable.ArrayBuilder

class RunStats {
  private val statsBldr = new SeriesStatsBuilder
  var ko = 0

  var minStart = Long.MaxValue
  var maxEnd = Long.MinValue

  def add(userId: Long, startTs: Long, endTs: Long, respTime: Int, status: String): Unit = {
    statsBldr.add(respTime)
    if (status != "OK") {
      ko += 1
    }
    if (startTs < minStart) {
      minStart = startTs
    }
    if (endTs > maxEnd) {
      maxEnd = endTs
    }
  }

  val log = LoggerFactory.getLogger(getClass)

  def fmt(v: Double) = {
    val targetL = 5
    val s1 = "%.1f".format(v)
    if (s1.length >= targetL)
      s1
    else {
      val dp = 1 + targetL - s1.length
      val s2 = s"%.${dp}f".format(v)
      var trimTo = s2.length - 1
      while (trimTo > 1 && s2(trimTo-1) != '.' && s2(trimTo) == '0') {
        trimTo -= 1
      }
      s2.substring(0, trimTo+1)
    }
  }

  def check(targetRps: Double) = {
    val stats = statsBldr.result()
    val ok = stats.len - ko
    val rps = (ok*1000.0)/(maxEnd.toDouble - minStart.toDouble)

    val result = rps >= targetRps*0.95
    
    log.info(s"rps=${fmt(rps)} (${fmt(100.0*rps/targetRps)}%), response med(ms): ${stats.med}, ok=$ok/${stats.len} (${fmt(100.0*ok/stats.len)}%), passed=$result")

    def cc2map(p: Product, pref: String) = {
      val values = p.productIterator
      p.getClass.getDeclaredFields.map(f => pref + f.getName -> values.next.toString).toMap
    }

    val resultsMap = Map(
      "rps" -> rps.toString,
      "passed" -> result.toString,
      "reqsOk" -> ok.toString,
      "reqsKo" -> ko.toString
    ) ++ cc2map(stats, "resptime.")

    (result, resultsMap)
  }
}

private class SeriesStatsBuilder {
  val buf = new ArrayBuilder.ofInt //FIXME probably not the best way to get stats
  def add(v: Int): Unit = {
    buf += v
  }
  def result() = {
    val r = buf.result()
    scala.util.Sorting.quickSort(r)
    IntSeriesStats(
      len = r.length,
      min = r(0),
      med = r(r.length/2))
  }
}

case class IntSeriesStats(len: Int, min: Int, med: Int)
