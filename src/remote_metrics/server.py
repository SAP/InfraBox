#!/usr/bin/env python
import cProfile
import sys
import time
import os
import requests

from prometheus_client import Gauge, start_http_server, parser

"""
A little python web server which collects datas from a distant Infrabox Prometheus instance and recreate them
to be used as a target by our main Prometheus Instance
For now it does not support histogram metrics, as we only get metrics created by our collector
server and the Node Exporter.
Quantiles and bucket are apparently not managed well with this kind of Federate scraping
Check https://prometheus.io/docs/prometheus/latest/federation/ for more details
"""


def family_iterator(text):
    """
    A parsing iterator to scrape the web page of a federate endpoint of a Prometheus server.
    It iterates over sample_iterator.
    """
    left_index = 0
    text_length = len(text)
    while left_index < text_length:
        if text[left_index] == "#":  # Metric declaration
            left_index += 7
            right_index = left_index + 1
            while text[right_index] != " ":  # Still in the metric name
                right_index += 1
            metric_name = text[left_index:right_index]
            left_index = right_index + 1
            while text[left_index] != "\n":
                left_index += 1

            yield metric_name, sample_iterator(text, [left_index])
        else:
            left_index += 1


def sample_iterator(text, ptr_index):
    """
    A sample iterator used to parse the web page of a federate endpoint of a Prometheus server.
    It iterates over tuples composed by :
    - a dictionnary of labels and their values
    - the corresponding sample value (always float)
    """
    label_dict = {}
    while text[ptr_index[0]] != "#":
        while text[ptr_index[0]] != "{":  # Searching for the start of the labels
            ptr_index[0] += 1
        ptr_index[0] += 1                 # We point to the first letter of the first label

        for label, value in label_iterator(text, ptr_index):
            label_dict[label] = value

        ptr_index[0] += 2  # We point at the value of the sample
        right_index = ptr_index[0] + 1
        while text[right_index] != " ":
            right_index += 1
        str_value = text[ptr_index[0]:right_index]
        if str_value == "NaN":
            value = 0
        else:
            value = float(str_value)

        yield label_dict, value

        ptr_index[0] = right_index
        while text[ptr_index[0]] != "\n":
            ptr_index[0] += 1
        ptr_index[0] += 1


def label_iterator(text, ptr_index):
    while text[ptr_index[0]] != "}":
        if text[ptr_index[0]] == ",":
            # We ensure pointing to the start of the label name
            ptr_index[0] += 1

        # We find the name
        right_index = ptr_index[0] + 1
        while text[right_index] != "=":
            right_index += 1
        name = text[ptr_index[0]:right_index]
        ptr_index[0] = right_index + 2

        # We find the value
        right_index += 3
        while text[right_index] != '"':
            right_index += 1
        value = text[ptr_index[0]:right_index]

        yield name, value

        ptr_index[0] = right_index + 1


class ScrapedGauge:
    def __init__(self, name, labels):
        self.name = name
        self.labels = tuple(labels[:])
        self._gauge = Gauge(name, "A identified metric found during scraping the /federate web page", list(self.labels))

    def update(self, label_values, value, prefix):
        start_time = time.time()
        self._gauge.labels(* self._label_value_iterator(label_values, prefix)).set(value)
        return time.time() - start_time

    def _label_value_iterator(self, label_values, prefix):
        for label in self.labels:
            if label != "instance":
                yield label_values.get(label)
            else:
                yield prefix + label_values.get(label)


class MetricManager:
    def __init__(self, prefix):
        self.metrics = dict()
        self.prefix = prefix + ":"
        self.total_set_time = 0

    def process(self, samples, name):
        """
        Set the values for the given family metric
        and create it if it has never been encountered before
        """
        metric = self.metrics.get(name)
        if metric:
            self._update(metric, samples)
        else:
            self._update(self._create(samples, name), samples)

    def _update(self, metric, samples):
        """
        Analyze the parsed labels and values and update the
        corresponding metric
        """
        for labels, value in samples:
            self.total_set_time += metric.update(labels, value, self.prefix)

    def _create(self, samples, name):
        """
        Analyze the parsed metric to create a proper metric
        """

        labels, value = next(samples)
        new_metric = ScrapedGauge(name, tuple(labels.keys()))
        self.metrics[name] = new_metric
        new_metric.update(labels, value, self.prefix)
        return new_metric


def start_server(init_wait_time, threshold, port):
    """
    A little utility which try to launch the server, is used at least one time.
    Could be use in the future in the TRY main statement if http server stops unexceptedly
    :param init_wait_time:  Time to wait the first time, is incremented at each fail
    :param threshold:       When the wait time get to this value we stop trying
    :param port:            Port on which open the server
    """
    print("Starting server on port : {}".format(port))
    while init_wait_time <= threshold:
        try:
            start_http_server(int(port))
            return True
        except OSError:
            # TODO find the right log where to write it
            sys.stderr.write(
                "Unable to start the server on the {} port\nI'll wait {}s and try again".format(port, init_wait_time))
            time.sleep(init_wait_time)
            init_wait_time += 1
    return False




def main():
    # getting the env variables
    server_port = os.environ.get('INFRABOX_PORT', 8044)
    distant_prom_addr = os.environ.get('DISTANT_PROM_ADDR', "http://local_host:9090")
    instance_prefix = os.environ.get('INSTANCE_LABEL_PREFIX', "distant")

    url_to_scrape = distant_prom_addr + '''/federate?match[]={__name__=~"..*"}'''

    # When restarting or starting on a docker container, the port can be still used at the first try
    if not start_server(2, 5, server_port):
        return 1

    # These are the metrics of the python collector server itself
    skipped_metrics = ('up', "scrape_samples_post_metric",
        "scrape_duration_seconds",
        "python_info",
        "process_virtual_memory_bytes",
        "process_start_time_seconds",
        "process_resident_memory_bytes",
        "process_open_fds",
        "process_max_fds",
        "process_cpu_seconds",
        'process_cpu_seconds_total')

    metric_manager = MetricManager(instance_prefix)
    while running:
        response = requests.get(url_to_scrape)
        web_text = response.content.decode("utf-8")
        families = family_iterator(web_text)
        for name, samples in families:
            if name not in skipped_metrics:
                metric_manager.process(samples, name)


if __name__ == '__main__':
    running = True
    main()

