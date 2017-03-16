package keystone_ltest

import ch.qos.logback.classic.LoggerContext
import ch.qos.logback.classic.encoder.PatternLayoutEncoder
import ch.qos.logback.classic.spi.ILoggingEvent
import ch.qos.logback.core.{ConsoleAppender, OutputStreamAppender, FileAppender}
import org.slf4j.{Logger, LoggerFactory}

object LogUtils {
  private def addAppender(appender: OutputStreamAppender[ILoggingEvent], immediateFlush: Boolean): Unit = {
    val ple = new PatternLayoutEncoder
    ple.setPattern("%d{HH:mm:ss.SSS} [%-5level] %logger{15} - %msg%n%rEx")

    val lc = LoggerFactory.getILoggerFactory.asInstanceOf[LoggerContext]
    ple.setContext(lc)
    ple.setImmediateFlush(immediateFlush)
    appender.setEncoder(ple)
    appender.setContext(lc)
    appender.start()
    ple.start()

    val rootLog = lc.getLogger(Logger.ROOT_LOGGER_NAME)
    rootLog.addAppender(appender)
  }
  def addAppender(path: String, immediateFlush: Boolean = false): FileAppender[ILoggingEvent] = {
    val appender = new FileAppender[ILoggingEvent]
    appender.setFile(path)
    appender.setAppend(true)
    addAppender(appender, immediateFlush)


    appender
  }
  def addConsoleAppender(): Unit = {
    val appender = new ConsoleAppender[ILoggingEvent]
    addAppender(appender, true)
  }
}
