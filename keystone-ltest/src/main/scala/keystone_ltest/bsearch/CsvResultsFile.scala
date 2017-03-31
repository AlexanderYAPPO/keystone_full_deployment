package keystone_ltest.bsearch

import java.io.BufferedWriter

import org.apache.commons.csv.{CSVPrinter, CSVFormat}

class CsvResultsFile(path: java.io.File) {
  var header: Array[String] = null
  var resultsCsv: BufferedWriter = null
  var csvPrinter: CSVPrinter = null

  private def printRow(row: Map[String, String]): Unit = {
    csvPrinter.printRecord(header.map(k => row.getOrElse(k, null)): _*)
  }

  def addResult(values: Map[String, String]): Unit = {
    //assumes that key set never changes
    if (header == null) {
      if (resultsCsv != null) {
        resultsCsv.close()
      }
      header = values.keys.toArray.sorted

      resultsCsv = java.nio.file.Files.newBufferedWriter(path.toPath, java.nio.charset.Charset.defaultCharset())
      csvPrinter = CSVFormat.DEFAULT.withHeader(header: _*).print(resultsCsv)
    }

    printRow(values)

    resultsCsv.flush()
  }

  def close(): Unit = {
    if (resultsCsv != null)
      resultsCsv.close()
  }
}
