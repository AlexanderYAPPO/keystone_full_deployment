package keystone_ltest

import io.gatling.core.Predef._
import io.gatling.http.Predef._

import scala.concurrent.duration._

class AuthenticateKeystoneTest extends Simulation {
  lazy val setup = new AuthKeystoneSetup

  val httpConf = http
    .baseURL(TestConfig.OS_AUTH_URL)
    .shareConnections

  val scn = scenario("auth")
      .group("auth") {
        exec(http("root")
        .get("")
        .check(status.is(200)))
          .exec(http("tokens")
            .post("/auth/tokens")
            .body(StringBody(session => setup.randomUserTokensJson))
            .header("Content-Type", "application/json")
            .check(status.is(201)))
    }

  TestConfig.authConf.runner.`type` match {
    case "rps" =>
      val rps = TestConfig.authConf.runner.rps
      val duration = TestConfig.authConf.runner.times.get.toDouble / rps

      val injSetup = constantUsersPerSec(rps) during(duration seconds)
      setUp(scn.inject(injSetup).protocols(httpConf)).maxDuration(duration * 1.2 seconds)
    case "rpsSteps" =>
      val rps = TestConfig.authConf.runner.rps
      val stepDuration = TestConfig.authConf.runner.step_duration.get
      val steps = TestConfig.authConf.runner.steps.get

      val injSetup = (1 to steps).map(x => constantUsersPerSec(x.toDouble/steps * rps) during (stepDuration seconds))
      setUp(scn.inject(injSetup).protocols(httpConf)).maxDuration(stepDuration * steps * 1.2 seconds)
  }
  
  before {
    setup
  }
  after {
    setup.cleanup()
  }
}
