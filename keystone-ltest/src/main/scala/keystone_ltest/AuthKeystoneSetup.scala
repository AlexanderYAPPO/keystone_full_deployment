package keystone_ltest

import java.util.Random
import java.util.concurrent.ThreadLocalRandom

import org.asynchttpclient.{Response, DefaultAsyncHttpClient}
import org.slf4j.LoggerFactory

import scala.util.{Failure, Success, Try}

class AuthKeystoneSetup {
  println("setup")
  val tenantName = "admin"
  val tenantId = "admin"
  val log = LoggerFactory.getLogger(this.getClass)
  val httpClient = new DefaultAsyncHttpClient


  import TestConfig._

  def tokensJson(username: String, password: String, domainName: String, projectName: String) =
    s"""
       |{
       |   "auth":{  
       |    "scope":{  
       |       "project":{  
       |          "domain":{  
       |             "name":"$domainName"
       |          },
       |          "name":"$projectName"
       |       }
       |    },
       |    "identity":{  
       |       "password":{  
       |          "user":{ 
       |             "domain":{  
       |                "name":"$domainName"
       |             },
       |             "password":"$password",
       |             "name":"$username"
       |          }
       |       },
       |       "methods":[  
       |          "password"
       |       ]
       |    }
       | }
       |}
       |
     """.stripMargin
    
  val tokensResp = reqWithRetry(new RequestFactory {
    override def newResp: Response = httpClient.preparePost(TestConfig.OS_AUTH_URL + "/auth/tokens")
      .setBody(tokensJson("admin", OS_PASSWORD, "Default", "admin"))
      .setHeader("Content-Type", "application/json")
      .execute().get()
    override def name: String = "get auth token"
  }).get
  assert(tokensResp.getStatusCode == 201)
  //val tokens = Json.parseStr[Json.TokensResp](tokensResp.getHeaders)
  val authToken = tokensResp.getHeader("X-Subject-Token")

  //val domainIdResp = reqWithRetry(new RequestFactory {
  //  override def newResp: Response = httpClient.prepareGet(TestConfig.OS_AUTH_URL + "/domains/admin")
  //    //.setBody(tokensJson(OS_TENANT_NAME, OS_USERNAME, OS_PASSWORD))
  //    .setHeader("X-Auth-Token", authToken)
  //    .execute().get()
  //  override def name: String = "get domain id"
  //}).get
  //assert(domainIdResp.getStatusCode == 200)
  //val domainBody = Json.parseStr[Json.DomainsResp](domainIdResp.getResponseBody)
  val domainId = "default"//domainBody.domain.id
  val domainName = "Default" //domainBody.domain.name
  //val authToken = tokensResp.getHeader("X-Subject-Token")
  

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
  
  val projectName = s"c_rally_${rndStr(8)}_${rndStr(8)}"
  def projectsJson(projectName: String, domainId: String) =
    s"""
       |{  
       | "project":{  
       | "enabled":true,
       | "domain_id":"$domainId",
       | "name":"$projectName"
       | }
       | }
     """.stripMargin

  val projectResp = reqWithRetry(new RequestFactory {
    override def newResp: Response = httpClient.preparePost(TestConfig.OS_AUTH_URL + "/projects")
      .setBody(projectsJson(projectName, domainId))
      .addHeader("Content-Type", "application/json")
      .addHeader("X-Auth-Token", authToken)
      .execute().get()
    override def name: String = "create project"
  }).get
  assert(projectResp.getStatusCode == 201)
  val projectId = Json.parseStr[Json.ProjectsResp](projectResp.getResponseBody).project.id


  //log.info(s"added tenant $tenantName, id=$tenantId")

  def addUser = {
    val name = s"c_rally_${rndStr(8)}_${rndStr(8)}"
    val pass = rndStr(34)
    def req(projectId: String, domainId: String) =
      s"""
         |{
         |   "user":{
         |      "password":"$pass",
         |      "enabled":true,
         |       "default_project_id": "$projectId",
         |      "name":"$name",
         |      "domain_id":"$domainId"
         |   }
         |}
       """.stripMargin
    val resp = reqWithRetry(new RequestFactory {
      override def newResp: Response = httpClient.preparePost(TestConfig.OS_AUTH_URL + "/users")
        .setBody(req(projectId, domainId))
        .setHeader("Content-Type", "application/json")
        .setHeader("X-Auth-Token", authToken)
        .execute().get()

      override def name: String = "create user"
    }).get
    assert(resp.getStatusCode == 201)
    println("^^^^^^^^^^^^^")
    val res = Json.parseStr[Json.UsersResp](resp.getResponseBody).user
    println("****************")
    //assert(res.name == name)
    //assert(res.username == name)

    //log.info(s"added user $name in tenant $tenantId")
    println(name, pass, res.id, domainName, projectName, projectId)
    val current_user = User(name, pass, res.id, domainName, projectName, projectId)
    giveRole(current_user)
    current_user
  }

 def giveRole(user: User) = {
    val roleIdResp = reqWithRetry(new RequestFactory {
    override def newResp: Response = httpClient.prepareGet(TestConfig.OS_AUTH_URL + "/roles")
      //.setBody(tokensJson(OS_TENANT_NAME, OS_USERNAME, OS_PASSWORD))
      .setHeader("X-Auth-Token", authToken)
      .execute().get()
    override def name: String = "get role id"
    }).get
    assert(roleIdResp.getStatusCode == 200)
    val roleBody = Json.parseStr[Json.RolesResp](roleIdResp.getResponseBody)
    var roleId = roleBody.roles(0).id  
    println(roleBody.roles(0).name)   
    if (roleBody.roles(0).name == "member"){
        roleId = roleBody.roles(1).id
        println(roleBody.roles(1).name) 
    }
    
    val resp = reqWithRetry(new RequestFactory {
      override def newResp: Response = httpClient.preparePut(TestConfig.OS_AUTH_URL + "/projects/" + user.projectId + "/users/" + user.id + "/roles/" + roleId)
        .setHeader("X-Auth-Token", authToken)
        .execute().get()

      override def name: String = "give role to user"
    }).get
    assert(resp.getStatusCode == 204)
    }

  println("####################")
  val users = (1 to TestConfig.users).map(_ => addUser).toArray
  println("%%%%%%%%%%%%%%%%%%%%%")
  //println(users)
  println(users.toString)

  def randomUser() = {
    users(ThreadLocalRandom.current().nextInt(users.length))
  }
  def randomUserTokensJson = {
    val user = randomUser()
    tokensJson(user.name, user.password, user.domain, user.project)
  }

  trait RequestFactory {
    def newResp: org.asynchttpclient.Response
    def name: String = ???
    def doneMsg: String = s"$name done"
    def badStatusMsg(resp: org.asynchttpclient.Response): String = {
      s"$reqFailedMsg, status=${resp.getStatusCode}/${resp.getStatusText}, body=${resp.getResponseBody}"
    }
    def reqFailedMsg: String = s"$name request failed"
    def allTriesFailedMsg: String = s"$name failed"

    def retryWait: Int = 30
  }

  def reqWithRetry(rf: RequestFactory, tries: Int = 1): Try[org.asynchttpclient.Response] = {
    var triesLeft = tries
    var lastFail: Throwable = null
    while (triesLeft > 0) {
      triesLeft -= 1
      val resp = Try(rf.newResp)
      if (resp.isFailure || !(200 to 206).contains(resp.get.getStatusCode)) {
        if (resp.isFailure) {
          log.warn(rf.reqFailedMsg, resp.failed.get)
          lastFail = new Exception(rf.reqFailedMsg, resp.failed.get)
        } else {
          log.warn(rf.badStatusMsg(resp.get))
          lastFail = new Exception(rf.badStatusMsg(resp.get))
        }
      } else {
        log.info(rf.doneMsg)
        return resp
      }
      if (triesLeft > 0 && rf.retryWait > 0) {
        log.info(s"waiting ${rf.retryWait}s")
        Thread.sleep(rf.retryWait * 1000)
      }
    }
    log.warn(rf.allTriesFailedMsg)
    Failure(lastFail)
  }

  def deleteUser(user: User, tries: Int = 1): Unit = {
    reqWithRetry(new RequestFactory {
      override def newResp: Response = {
        httpClient.prepareDelete(TestConfig.OS_AUTH_URL + "/users/" + user.id)
          .setHeader("X-Auth-Token", authToken)
          .execute().get()
      }

      override def doneMsg: String = s"removed user ${user.name}, id=${user.id}"
      override def reqFailedMsg: String = "delete user request failed"
      override def allTriesFailedMsg: String = s"failed to delete user ${user.name}, id=${user.id}"
    }, tries)
  }

  def deleteTenant(tries: Int = 1): Unit = {
    reqWithRetry(new RequestFactory {
      override def newResp: Response = {
        httpClient.prepareDelete(TestConfig.OS_AUTH_URL + "/projects/" + tenantId)
          .setHeader("X-Auth-Token", authToken)
          .execute().get()
      }

      override def doneMsg: String = s"removed tenant $tenantId"
      override def reqFailedMsg: String = "delete tenant request failed"
      override def allTriesFailedMsg: String = s"failed to remove tenant $tenantId"
    }, tries)
  }

  def cleanup(): Unit = {
    //users.foreach(deleteUser(_))

    //deleteTenant()
  }
}

case class User(name: String, password: String, id: String, domain: String, project: String, projectId: String)

object Json {
  import org.json4s._
  import org.json4s.jackson.JsonMethods._
  implicit val formats = DefaultFormats

  def parseStr[A](str: String)(implicit m: Manifest[A]) = parse(str).extract[A]

  case class TokensResp(access: AccessObj)
  case class AccessObj(token: TokenObj, serviceCatalog: Any)
  case class TokenObj(issued_at: String, expires: String, id: String, tenant: Any, audit_ids: Any)

  //case class TenantsResp(tenant: TenantObj)
  //case class TenantObj(name: String, id: String)

  case class DomainsResp(domain: DomainObj)
  case class DomainObj(name: String, id: String)

  case class ProjectsResp(project: ProjectObj)
  case class ProjectObj(name: String, id: String)
    
  case class RoleObj(id: String, name: String)
  case class RolesResp(roles: List[RoleObj], links: LinksObj)
  //case class StuffObj(roles: List[RoleObj], links: LinksObj)
  case class LinksObj(next: String)
  

  case class UsersResp(user: UserObj)
  case class UserObj(id: String, enabled: Boolean, name: String)
}
