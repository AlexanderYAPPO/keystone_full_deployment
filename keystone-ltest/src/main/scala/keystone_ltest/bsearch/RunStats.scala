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

  def ok(targetRps: Double) = {
    val stats = statsBldr.result()
    val rps = (stats.len*1000.0)/(maxEnd.toDouble - minStart.toDouble)

    val result = ko == 0 && rps >= targetRps*0.9 && stats.med < 1000

    log.info(s"rps=$rps, response med(ms): ${stats.med}, ok=${stats.len-ko}/${stats.len}, passed=$result")

    result
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
