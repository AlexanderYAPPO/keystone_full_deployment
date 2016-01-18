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


def G():
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
                yield task



def run_playbook(name, extra):
    name = name
    extra_vars = extra

def read_json(rps): # zaglushka
    return True # True/False
def save(rps):
    print "saved"

class Runner:
    def __init__(self, task):
        self.LIST = task["list"]
        self.arg = None

    def parse(self, task):
        action = task.action
        name = task.name
        if action == "mount":
            params = {"fs_type" : name }
            run_playbook(name, params)
        if action == "run" or "stop":
            params = {}
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
    pass

if __name__ == "__main__":
    cmd_parse()
    gen = G()
    for task in gen:
        runner = Runner(task)
        N = bin_search(task)
        # runner.LIST[4] = t("func", "save")
        # runner.execute()
        print "N = %s" % N




