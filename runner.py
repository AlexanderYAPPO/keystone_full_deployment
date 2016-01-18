__author__ = 'student'



WEB_SERVERS = ["apache", "uwsgi"]
DBMS = ["postgresql", "mysql"]  # database type
FS = ("/dev/sda7",  # HDD
          "tmpfs",  # overlay
          "/dev/sdb1"  # SSD
          )


class t:
    def __init__(self, action, name):
        self.action = action
        self.name = name


class GE:
    def __init__(self, act):
        self.i = 0
        self.L = []
        if act == "install":
            LIST = [
                t("install", "tests"),
                t("install", "postgresql"),
                t("install", "mysql"),
                t("install", "keystone"),
                t("install", "apache"),
                t("install", "uwsgi"),
                t("install", "rally")
                ]
            task = {"list": LIST}
            self.L.append(task)

        if act == "run":
            for db in DBMS:
                for srv in WEB_SERVERS:
                    for fs in FS:
                        LIST =  [
                                t("mount", fs),
                                t("run", db),
                                t("run", srv),
                                t("run", "keystone"),
                                t("func", "tests"),
                                t("stop", "keystone"),
                                t("stop", srv),
                                t("stop", db),
                                t("umount", fs)
                                ]
                        task = {"list": LIST,
                                "param1": 0,
                                "param2": 20
                        }
                        self.L.append(task)
        self.n = len(self.L)

    def get_savetask(self):
        cur = self.i - 1
        for index, item in enumerate(self.L[cur]["list"]):
            if item.name == "tests":
                item.name = "save"
                self.L[cur]["list"][index] = item
        return self.L[cur]

    def __iter__(self):
        return self

    def next(self):
        if self.i < self.n:
            i = self.i
            self.i += 1
            return self.L[i]
        else:
            raise StopIteration()


def run_playbook(name, extra):
    name = name
    extra_vars = extra

def read_json(rps): # zaglushka
    print("read")
    return True # True/False

def save(rps):
    print "saved", rps

class Runner:
    def __init__(self, task):
        self.LIST = task["list"]
        self.arg = None

    def parse(self, task):
        action = task.action
        name = task.name
        params = {}
        if action == "mount":
            params = {"fs_type" : name }
            run_playbook(name, params)

        if action == "run" or "stop" or "install":
            run_playbook("%s_%s" % (action, name), params)

        if action == "func":
            if name == "tests":
                rps = self.arg
                return read_json(rps)
            if name == "save":
                rps = self.arg
                return save(rps)


    def execute(self):
        result = None
        for task in self.LIST:
            res = self.parse(task)
            if res != None:
                result = res
        print "executed:"
        print [(x.action, x.name) for x in self.LIST]
        return result



def bin_search(task):
    left = task["param1"]
    right = task["param2"]
    while True:
        m = int((left + right) / 2)
        runner.arg = m
        result = runner.execute()
        if result:
            right = m
        else:
            left = m
        if right == left + 1:
            return left


def cmd_parse():
    return 0

if __name__ == "__main__":
    inst = cmd_parse()
    if inst:
        install_gen = GE("install")
        for task in install_gen:
            runner = Runner(task)
            runner.execute()

    run_gen = GE("run")
    for task in run_gen:
        runner = Runner(task)
        N = bin_search(task)
        print "N = %s" % N
        save_task = run_gen.get_savetask()
        for rps in (N - 1, N, N + 1, N + 3, N + 5, 2 * N):
            save_runner = Runner(save_task)
            save_runner.arg = rps
            save_runner.execute()

