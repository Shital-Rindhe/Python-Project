import json
import sys
import requests
from jinja2 import Template


TEMPLATE = "Template/sonar-qube.html"
URL = "http://10.12.6.31:9000/api/measures/component?additionalFields=metrics," \
      "periods&component=Test:CLSPoc&metricKeys=complexity,duplicated_lines_density," \
      "violations,code_smells,bugs,comment_lines_density,files,lines,ncloc,functions,statements,coverage"


def sonar(module):
    with open('config_data.json') as f:
        data = json.load(f)
    print(data)
    return data

if __name__ == '__main__':
    global list
    list=[]
    module_list = ["abcd", "ghfkf"]
    for module in module_list:
        response = sonar(module)
        list.append(response)
    print(list)
    with open('sonarqube.html', "w+") as f:
        f.write(Template(open(TEMPLATE).read()).render(module_details=list))



    # component = sys.argv[1]
    # r = requests.get(URL, headers={'Cache-Control': 'no-cache'})
    # if r.status_code == 200:
    #     data = r.json()
    #     with open('config_data.json', 'w', encoding='utf-8') as f:
    #         json.dump(data, f, ensure_ascii=False, indent=4)
    # else:
    #     print("Sonar API access issue.")

    # try:
    #     with open('config_data.json') as json_file:
    #         data = json.load(json_file)
    # except Exception as e:
    #     print(e)


    # for key in data['component']:
    #     dict[key['measures']['metric']] = key['value']
    #     obj_list.append(dict)
        # dict.clear()
    # print(obj_list)
    # with open('sonarqube.html', "w+") as f:
    #     # f.write(Template(open(TEMPLATE).read()).render(summary=dict, version=version_in, project_name=data['component']['name']))
    #     f.write(Template(open(TEMPLATE).read()).render(summary=dict, project_name="fgdhd"))
