package keystone_ltest

import java.io.File

object TestConfig {
  import org.json4s._
  import org.json4s.jackson.JsonMethods._
  implicit val formats = DefaultFormats

  val authConfList = {
    (parse(new FileInput(new File("sc.json"))) \ "Authenticate.keystone").asInstanceOf[JArray]
  }

  assert(authConfList.arr.length == 1)
  val authConf = authConfList(0).extract[AuthConf]

  assert(authConf.context.users.tenants == 1)
  val users = authConf.context.users.users_per_tenant

  val OS_AUTH_URL = Option(System.getenv("OS_AUTH_URL")).getOrElse("http://127.0.0.1:35357/v2.0")
  val OS_TENANT_NAME = Option(System.getenv("OS_TENANT_NAME")).getOrElse("admin")
  val OS_USERNAME = Option(System.getenv("OS_USERNAME")).getOrElse("admin")
  val OS_PASSWORD = Option(System.getenv("OS_PASSWORD")).getOrElse("admin")
}

case class AuthConf(runner: RunnerConf, context: ContextConf)

case class RunnerConf(rps: Double, `type`: String, times: Option[Int], step_duration: Option[Double], steps: Option[Int])
case class ContextConf(users: UserContextConf)
case class UserContextConf(users_per_tenant: Int, tenants: Int)
