package keystone_ltest

import java.util.Random
import java.util.concurrent.ThreadLocalRandom

import org.asynchttpclient.DefaultAsyncHttpClient
import org.slf4j.LoggerFactory

class AuthKeystoneSetup {
  val log = LoggerFactory.getLogger(this.getClass)
  val httpClient = new DefaultAsyncHttpClient

  import TestConfig._

  def tokensJson(tenantName: String, username: String, password: String) =
    s"""
       |{
       |   "auth":{
       |      "tenantName":"$tenantName",
       |      "passwordCredentials":{
       |         "username":"$username",
       |         "password":"$password"
       |      }
       |   }
       |}
       |
     """.stripMargin

  val tokensResp = httpClient.preparePost(TestConfig.OS_AUTH_URL + "/tokens")
    .setBody(tokensJson(OS_TENANT_NAME, OS_USERNAME, OS_PASSWORD))
    .setHeader("Content-Type", "application/json")
    .execute().get()
  assert(tokensResp.getStatusCode == 200)
  val tokens = Json.parseStr[Json.TokensResp](tokensResp.getResponseBody)
  val authToken = tokens.access.token.id

  def tenantsJson(name: String) =
    s"""
       |{
       |   "tenant":{
       |      "enabled":true,
       |      "name":"$name",
       |      "description":null
       |   }
       |}
     """.stripMargin

  val rnd = new Random
  val alphanumChars = (('a' to 'z') ++ ('A' to 'Z') ++ ('0' to '9')).mkString("")
  def rndChar = {
    alphanumChars(rnd.nextInt(alphanumChars.length))
  }

  def rndStr(length: Int) = {
    val chars = new Array[Char](length)
    for (i <- chars.indices) {
      chars(i) = rndChar
    }
    new String(chars)
  }

  val tenantName = s"c_rally_${rndStr(8)}_${rndStr(8)}"

  val tenantsResp = httpClient.preparePost(TestConfig.OS_AUTH_URL + "/tenants")
    .setBody(tenantsJson(tenantName))
    .addHeader("Content-Type", "application/json")
    .addHeader("X-Auth-Token", authToken)
    .execute().get()
  assert(tenantsResp.getStatusCode == 200)
  val tenantId = Json.parseStr[Json.TenantsResp](tenantsResp.getResponseBody).tenant.id

  log.info(s"added tenant $tenantName, id=$tenantId")

  def addUser = {
    val name = s"c_rally_${rndStr(8)}_${rndStr(8)}"
    val pass = rndStr(34)
    val req =
      s"""
         |{
         |   "user":{
         |      "email":"$name@email.me",
         |      "password":"$pass",
         |      "enabled":true,
         |      "name":"$name",
         |      "tenantId":"${tenantId}"
         |   }
         |}
       """.stripMargin
    val resp = httpClient.preparePost(TestConfig.OS_AUTH_URL + "/users")
      .setBody(req)
      .setHeader("Content-Type", "application/json")
      .setHeader("X-Auth-Token", authToken)
      .execute().get()
    assert(resp.getStatusCode == 200)
    val res = Json.parseStr[Json.UsersResp](resp.getResponseBody).user
    assert(res.name == name)
    assert(res.username == name)

    log.info(s"added user $name in tenant $tenantId")

    User(name, pass, res.id)
  }

  val users = (1 to TestConfig.users).map(_ => addUser).toArray

  def randomUser() = {
    users(ThreadLocalRandom.current().nextInt(users.length))
  }
  def randomUserTokensJson = {
    val user = randomUser()
    tokensJson(tenantName, user.name, user.password)
  }

  def deleteUser(user: User, tries: Int = 3): Unit = {
    var triesLeft = tries
    while (triesLeft > 0) {
      triesLeft -= 1
      val resp = httpClient.prepareDelete(TestConfig.OS_AUTH_URL + "/users/" + user.id)
        .setHeader("X-Auth-Token", authToken)
        .execute().get()
      if (resp.getStatusCode != 200) {
        log.warn(s"delete user request failed, status=${resp.getStatusCode}/${resp.getStatusText}, body=${resp.getResponseBody}")
      } else {
        log.info(s"removed user ${user.name}, id=${user.id}")
        return
      }
    }
    log.warn(s"failed to delete user ${user.name}, id=${user.id}")
  }

  def deleteTenant(tries: Int = 3): Unit = {
    var triesLeft = tries
    while (triesLeft > 0) {
      triesLeft -= 1
      val resp = httpClient.prepareDelete(TestConfig.OS_AUTH_URL + "/tenants/" + tenantId)
        .setHeader("X-Auth-Token", authToken)
        .execute().get()
      if (resp.getStatusCode != 200) {
        log.warn(s"delete tenant request failed, status=${resp.getStatusCode}/${resp.getStatusText}, body=${resp.getResponseBody}")
      } else {
        log.info(s"removed tenant $tenantId")
        return
      }
    }
    log.warn(s"failed to remove tenant $tenantId")
  }

  def cleanup(): Unit = {
    users.foreach(deleteUser(_))

    deleteTenant()
  }
}

case class User(name: String, password: String, id: String)

object Json {
  import org.json4s._
  import org.json4s.jackson.JsonMethods._
  implicit val formats = DefaultFormats

  def parseStr[A](str: String)(implicit m: Manifest[A]) = parse(str).extract[A]

  case class TokensResp(access: AccessObj)
  case class AccessObj(token: TokenObj, serviceCatalog: Any)
  case class TokenObj(issued_at: String, expires: String, id: String, tenant: Any, audit_ids: Any)

  case class TenantsResp(tenant: TenantObj)
  case class TenantObj(name: String, id: String)

  case class UsersResp(user: UserObj)
  case class UserObj(id: String, enabled: Boolean, name: String, username: String)
}
