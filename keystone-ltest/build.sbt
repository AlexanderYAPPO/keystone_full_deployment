name := "keystone-ltest"

version := "1.0"

scalaVersion := "2.11.8"

scalacOptions += "-target:jvm-1.8"

enablePlugins(GatlingPlugin)

javaOptions in GatlingIt := overrideDefaultJavaOptions("-Xms8g", "-Xmx8g")

libraryDependencies += "io.gatling.highcharts" % "gatling-charts-highcharts" % "2.2.4" % "test,it"
libraryDependencies += "io.gatling" % "gatling-test-framework" % "2.2.4" % "test,it"
libraryDependencies += "org.json4s" %% "json4s-jackson" % "3.5.0" % "test,it"
