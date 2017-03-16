package keystone_ltest

import ch.qos.logback.classic.LoggerContext
import ch.qos.logback.classic.encoder.PatternLayoutEncoder
import ch.qos.logback.classic.spi.ILoggingEvent
import ch.qos.logback.core.FileAppender
import org.slf4j.{Logger, LoggerFactory}

object LogUtils {
  def addAppender(path: String) = {
    val ple = new PatternLayoutEncoder
    ple.setPattern("%d{HH:mm:ss.SSS} [%-5level] %logger{15} - %msg%n%rEx")

    val lc = LoggerFactory.getILoggerFactory.asInstanceOf[LoggerContext]
    ple.setContext(lc)
    ple.setImmediateFlush(false)

    val appender = new FileAppender[ILoggingEvent]
    appender.setFile(path)
    appender.setEncoder(ple)
    appender.setContext(lc)
    appender.setAppend(true)
    appender.start()
    ple.start()

    val rootLog = lc.getLogger(Logger.ROOT_LOGGER_NAME)
    rootLog.addAppender(appender)

    appender
  }
}
