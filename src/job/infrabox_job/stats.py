import threading
import time
import docker

class StatsCollector(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.data = {}
        self.container_worker = threading.Thread(target=self.list_containers)
        self.container_worker.start()
        self.run = True

    def stop(self):
        with self.lock:
            self.run = False

    def get_result(self):
        result = {}
        with self.lock:
            for name in self.data:
                d = self.data[name]
                result[name] = d['stats']

        return result

    def handle_stat(self, prev, current):
        if not prev:
            return

        cpu_container_prev = prev['cpu_stats']['cpu_usage']['total_usage']
        cpu_container_cur = current['cpu_stats']['cpu_usage']['total_usage']

        cpu_system_cur = current['cpu_stats']['system_cpu_usage']
        cpu_system_prev = prev['cpu_stats']['system_cpu_usage']

        cpu_delta = float(cpu_container_cur) - float(cpu_container_prev)
        system_delta = float(cpu_system_cur) - float(cpu_system_prev)

        cpu_percent = (cpu_delta / system_delta) * len(current['cpu_stats']['cpu_usage']['percpu_usage']) * 100
        cpu_percent = float(int(cpu_percent * 100)) / 100.0

        # handle mem
        mem_total = float(current['memory_stats']['usage']) / 1024 / 1024
        mem_total = float(int(mem_total * 100)) / 100.0

        return {"cpu": cpu_percent, "mem": mem_total, "date": int(time.time())}


    def get_stats(self, container_data):
        c = container_data['container']
        try:
            for current in c.stats(decode=True):
                with self.lock:
                    if not self.run:
                        return

                stat = self.handle_stat(container_data['prev'], current)
                container_data['prev'] = current

                if stat:
                    container_data['stats'].append(stat)
        except:
            pass


    def list_containers(self):
        client = docker.from_env(version="1.24", timeout=3)
        while True:
            time.sleep(1)

            containers = []
            try:
                containers = client.containers.list()
            except:
                pass

            with self.lock:
                if not self.run:
                    return

                for c in containers:
                    if c.name in self.data:
                        continue

                    container_data = {
                        "prev": None,
                        "stats": [],
                        "thread": None,
                        "container": c
                    }

                    container_data['thread'] = threading.Thread(target=self.get_stats, args=(container_data,))
                    container_data['thread'].start()
                    self.data[c.name] = container_data
