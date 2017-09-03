import shutil
import argparse
import subprocess
import time
import os
import json
import textwrap
import requests
from colorama import Fore

summary = {
    "High": 0,
    "Medium": 0,
    "Low": 0,
    "Unknown": 0,
    "Unhandled": 0,
    "Negligible": 0
}

colors = {
    "High": Fore.RED,
    "Medium": Fore.YELLOW,
    "Low": Fore.WHITE,
    "Unknown": Fore.WHITE,
    "Unhandled": Fore.RED,
    "Negligible": Fore.WHITE
}

colors_json = {
    "High": "red",
    "Medium": "orange",
    "Low": "yellow",
    "Unknown": "grey",
    "Unhandled": "red",
    "Negligible": "grey"
}

priorities = {
    "Unhandled": 6,
    "High": 5,
    "Medium": 4,
    "Low": 3,
    "Unknown": 2,
    "Negligible": 01
}


def execute(command, cwd=None):
    process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, universal_newlines=True)

    # Poll process for new output until finished
    while True:
        line = process.stdout.readline()
        if not line:
            break

        print line.rstrip()

    process.wait()

    exitCode = process.returncode
    if exitCode != 0:
        raise Exception(exitCode)

def save(args):
    out_path = os.path.join(args.path, 'image')
    execute(('docker', 'save', '-o', out_path, args.image))
    execute(('tar', 'xf', out_path), cwd=args.path)

def get_layers(args):
    manifest_path = os.path.join(args.path, 'manifest.json')
    with open(manifest_path) as f:
        manifest = json.load(f)
    layers = []

    for l in manifest[0]['Layers']:
        layers.append(l.split("/layer.tar")[0])

    return layers

def analyze_layer(path, layer, parent):
    payload = {
        "Layer": {
            "Name": layer,
            "Path": path,
            "ParentName": parent,
            "Format": "Docker"
        }
    }

    while True:
        try:
            r = requests.get("http://127.0.0.1:6061", timeout=300)
            break
        except:
            time.sleep(5)

    r = requests.post("http://127.0.0.1:6060/v1/layers", data=json.dumps(payload), timeout=300)
    r.json()

def analyze(args, layers):
    for i in xrange(0, len(layers)):

        if i > 0:
            parent = layers[i-1]
        else:
            parent = ""

        p = os.path.join(args.path, layers[i], 'layer.tar')
        analyze_layer(p, layers[i], parent)

def get_layer(layer):
    url = "http://127.0.0.1:6060/v1/layers/%s?vulnerabilities" % layer
    r = requests.get(url)
    return r.json()

def print_console(vulnerabilities):
    print "Summary:"
    print "Found %s vulnerabilities" % len(vulnerabilities)
    print "%sHigh%s: %s" % (Fore.RED, Fore.RESET, summary['High'])
    print "%sMedium%s: %s" % (Fore.GREEN, Fore.RESET, summary['Medium'])
    print "%sLow%s: %s" % (Fore.WHITE, Fore.RESET, summary['Low'])
    print "%sNegligible%s: %s" % (Fore.WHITE, Fore.RESET, summary['Negligible'])
    print "%sUnknown%s: %s" % (Fore.WHITE, Fore.RESET, summary['Unknown'])
    print
    print

    for vul in vulnerabilities:
        v = vul['vulnerability']
        f = vul['feature']
        print "%s (%s%s%s)" % (v['Name'], colors[v['Severity']], v['Severity'], Fore.RESET)

        if "Description" in v:
            lines = textwrap.wrap(v['Description'], 80)
            for l in lines:
                print "\t%s" % l

            print

        print "\t%s @ %s" % (f['Name'], f['Version'])

        if "FixedBy" in v:
            print "\tFixed version: %s" % v['FixedBy']

        if "Link" in v:
            print "\tFixed Link:    %s" % v['Link']


        print "\tLayer:         %s" % f['AddedBy']
        print

def print_infrabox_json(args, vulnerabilities):
    rows = []
    available_fixes = 0
    for vul in vulnerabilities:
        v = vul['vulnerability']
        f = vul['feature']

        fixed_by = " "
        if "FixedBy" in v:
            fixed_by = v['FixedBy']
            available_fixes += 1

        rows.append([{
            "type": "text",
            "text": v['Name']
        }, {
            "type": "group",
            "elements": [{
                "type": "icon",
                "name": "fa-exclamation-triangle",
                "color": colors_json[v['Severity']],
            }, {
                "type": "text",
                "color": colors_json[v['Severity']],
                "text": v['Severity']
            }]
        }, {
            "type": "text",
            "text": f['Name']
        }, {
            "type": "text",
            "text": f['Version']
        }, {
            "type": "text",
            "text": fixed_by
        }])

    # Heading - Summary
    page_elements = [{
        "type": "h1",
        "text": "Summary"
    }]

    # Table - Symmary
    summary_table = {
        "type": "table",
        "rows": [
            [{
                "type": "icon",
                "name": "fa-exclamation-triangle",
                "color": "red"
            }, {
                "type": "text",
                "text": "High",
                "color": "red"
            }, {
                "type": "text",
                "text": str(summary['High'])
            }],
            [{
                "type": "icon",
                "name": "fa-exclamation-triangle",
                "color": "orange"
            }, {

                "type": "text",
                "text": "Medium",
                "color": "orange"
            }, {
                "type": "text",
                "text": str(summary['Medium'])
            }],
            [{
                "type": "icon",
                "name": "fa-exclamation-triangle",
                "color": "yellow"
            }, {

                "type": "text",
                "text": "Low",
                "color": "yellow"
            }, {
                "type": "text",
                "text": str(summary['Low'])
            }],
            [{
                "type": "icon",
                "name": "fa-exclamation-triangle",
            }, {

                "type": "text",
                "text": "Negligible",
            }, {
                "type": "text",
                "text": str(summary['Negligible'])
            }],
            [{
                "type": "icon",
                "name": "fa-exclamation-triangle",
            }, {

                "type": "text",
                "text": "Unknown",
            }, {
                "type": "text",
                "text": str(summary['Unknown'])
            }]
        ]
    }

    pie_chart = {
        "type": "pie",
        "name": "Vulnerabilities",
        "data": [{
            "label": "High",
            "color": "red",
            "value": summary['High']
        }, {
            "label": "Medium",
            "color": "orange",
            "value": summary['Medium']
        }, {
            "label": "Low",
            "color": "yellow",
            "value": summary['Low']
        }, {
            "label": "Negligible",
            "color": "grey",
            "value": summary['Negligible']
        }, {
            "label": "Unknown",
            "color": "grey",
            "value": summary['Unknown']
        }]
    }

    right_layout_group = {
        "type": "group",
        "elements": [{
            "type": "h2",
            "text": "Security Scanner has detected %s vulnerabilities" % len(vulnerabilities)
        }, {
            "type": "h2",
            "text": "Patches are available for %s vulnerabilities" % available_fixes
        }, summary_table]
    }

    layout_table = {
        "type": "grid",
        "rows": [[pie_chart, right_layout_group]]
    }

    page_elements.append(layout_table)

    page_elements.append({
        "type": "h1",
        "text": "Image Vulnerabilities"
    })

    headers = [{
        "type": "text",
        "text": "CVE"
    }, {
        "type": "text",
        "text": "Severity"
    }, {
        "type": "text",
        "text": "Package"
    }, {
        "type": "text",
        "text": "Current Version"
    }, {
        "type": "text",
        "text": "Fixed in Version"
    }]

    page_elements.append({
        "type": "table",
        "headers": headers,
        "rows": rows
    })

    data = {
        "version": 1,
        "title": "Container Scan",
        "elements": page_elements
    }

    with open(args.output, "w+") as out:
        json.dump(data, out)

def main():
    parser = argparse.ArgumentParser(description='Analyze images with clair')
    parser.add_argument('--image', required=True, help='the image to analyze')
    parser.add_argument('--path', help='path where the image is stored', default='/tmp/analyze')
    parser.add_argument('--output', help='path to the outpout markdown file',
                        default='/infrabox/upload/markdown/container_scan.md')

    args = parser.parse_args()

    if os.path.exists(args.path):
        shutil.rmtree(args.path)

    os.makedirs(args.path)

    save(args)
    layers = get_layers(args)
    analyze(args, layers)
    layer = get_layer(layers[-1])['Layer']

    if "Features" not in layer:
        print "No features have been detected in the image."
        print "This usually means that the image isn't supported by Clair"

        with open(args.output, "w+") as out:
            data = {
                "version": 1,
                "title": "Container Scan",
                "elements": [{
                    "type": "h3",
                    "text": "No features have been detected in the image"
                }, {
                    "type": "h3",
                    "text": "This usually means that the image isn't supported by Clair"
                }]
            }

            json.dump(data, out)

        return

    vulnerabilities = []

    for feature in layer['Features']:
        if 'Vulnerabilities' not in feature:
            continue

        for v in feature['Vulnerabilities']:
            sev = v['Severity']

            if sev not in summary:
                summary['Unhandled'] += 1
                v['Severity'] = 'Unhandled'
            else:
                summary[sev] += 1

            vulnerabilities.append({
                "vulnerability": v,
                "feature": feature
            })

    vulnerabilities.sort(key=lambda x: priorities[x['vulnerability']['Severity']], reverse=True)
    print_console(vulnerabilities)
    print_infrabox_json(args, vulnerabilities)

if __name__ == "__main__":
    main()
