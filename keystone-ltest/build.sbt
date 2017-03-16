name := "keystone-ltest"

version := "1.0"

scalaVersion := "2.11.8"

scalacOptions += "-target:jvm-1.8"

mergeStrategy in assembly := {
  case x if x.endsWith("io.netty.versions.properties") => MergeStrategy.first
  case x =>
    val oldStrategy = (assemblyMergeStrategy in assembly).value
    oldStrategy(x)
}

libraryDependencies += "io.gatling.highcharts" % "gatling-charts-highcharts" % "2.2.4"
libraryDependencies += "io.gatling" % "gatling-test-framework" % "2.2.4"
libraryDependencies += "org.json4s" %% "json4s-jackson" % "3.5.0"
