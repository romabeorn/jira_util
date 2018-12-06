import json
import re
import requests
import urllib.parse
import webbrowser
import xlrd

structure_list = ('Big Conference VM',
                  'Test Android VM SDK',
                  'Test IOS VM SDK',
                  'Test SB 1',
                  'Test SB 2',
                  'Test TS IM mobile',
                  'Test TS IM PC',
                  'Test TSPC basic',
                  'Test Videomost Space',
                  'Test VM Disk',
                  'Test VM Mobile',
                  'Test VM Smoke',
                  'Test МТС Телемед',
                  'Test РУССОФТ',
                  'TSM smoke test')

structure_json = {
    "1": '20',
    "2": '10',
    "3": '13',
    "4": '8',
    "5": '9',
    "6": '1',
    "7": '17',
    "8": '16',
    "9": '18',
    "10": '15',
    "11": '7',
    "12": '3',
    "13": '19',
    "14": '11',
    "15": '6'
}

data = {
    'forestSpec': '{"structureId": ""}',
    'viewSpec': {
        "columns": [
            {
                "csid": "handle",
                "key": "handle"
            },
            {
                "name": "Key",
                "key": "field",
                "csid": "1",
                "params": {
                    "field": "issuekey"
                }
            },
            {
                "name": "Summary",
                "key": "main",
                "csid": "main",
                "params": {

                }
            },
            {
                "name": "Progress",
                "key": "progress",
                "csid": "2",
                "params": {
                    "basedOn": "timetracking",
                    "resolvedComplete": True,
                    "includeSelf": True
                }
            },
            {
                "key": "icons",
                "name": "TP",
                "csid": "3",
                "params": {
                    "fields": [
                        "issuetype",
                        "priority"
                    ]
                }
            },
            {
                "name": "",
                "key": "com.almworks.testy.status",
                "params": {
                    "aggregateSeparate": True,
                    "showUsers": True,
                    "notes": {
                        "enabled": True,
                        "autoExpand": True
                    },
                    "testRunId": None
                },
                "csid": "#1"
            },
            {
                "csid": "actions",
                "key": "actions"
            }
        ]
    },
    'expand': '10000'
}

headers = {
    'X-Atlassian-Token': 'no-check',
    'Host': 'jira.spiritcorp.com',
    'Origin': 'http://jira.spiritcorp.com',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Referer': 'http://jira.spiritcorp.com/secure/StructureBoard.jspa?s=',
    'Accept-Encoding': 'gzip, deflate',
}

jql_data = {'jql': '', 'decorator': None}

structure_test_runs = {

}

class JiraUtil:
    def __init__(self, post_json_data):
        try:
            self.data = post_json_data
            self.json_of_testcases_failed_or_blocked = {}
            self.json_of_testcases = {}
            self.structure_id = ''
            self.bugs_list = list()
            self.failed_or_blocked_notes_without_bug = list()
            self.test_run_name = input('Введите название тестового прогона: ')
            if self.test_run_name.isdigit():
                try:
                    self.test_run_name = structure_test_runs[self.test_run_name]
                except:
                    print('Неправильный порядковый номер')
                    exit()
            self.data["viewSpec"]["columns"][-2]["name"] = self.test_run_name
            self.url = 'http://jira.spiritcorp.com/plugins/servlet/structure/excel HTTP/1.1'
            self.test_run_id = CommunicateWithJira.get_test_run_id_by_name(self.test_run_name)
            if self.test_run_id:
                self.data["viewSpec"]["columns"][-2]["params"]["testRunId"] = self.test_run_id
            else:
                raise ValueError
            self.encoded_data = Code.encode(self.data)
        except ValueError:
            print('Не существует такого тестового прогона в Jira!')
            exit()
        except:
            print('Произошла ошибка')

    def analyze_xls(self):
        try:
            workbook = xlrd.open_workbook(self.test_run_name + ".xls")
            sheet = workbook.sheet_by_index(0)
            self.get_json_of_testcases(sheet.col_values(0), sheet.col_values(5))
            self.get_json_of_testcases_failed_or_blocked()
            self.get_list_of_bugs_in_notes()
        except:
            print("Загруженный xls поврежден или его не существует")
            exit()

    def get_json_of_testcases(self, keys, stat):
        for i in range(1, len(keys)):
            if keys[i] != '':
                self.json_of_testcases[keys[i]] = stat[i]

    def get_json_of_testcases_failed_or_blocked(self):
        for i in self.json_of_testcases:
            if self.json_of_testcases[i].startswith('FAILED') or self.json_of_testcases[i].startswith('BLOCKED'):
                self.json_of_testcases_failed_or_blocked[i] = self.json_of_testcases[i]

    def print_json(self):
        for i in self.json_of_testcases_failed_or_blocked:
            print('---------------------------------------------------------------')
            print('ISSUE: ' + i)
            print(self.json_of_testcases_failed_or_blocked[i])
            print()

    def get_list_of_bugs_in_notes(self):
        pattern = re.compile('\w+-\d+')
        for i in self.json_of_testcases_failed_or_blocked:
            matches = pattern.findall(self.json_of_testcases_failed_or_blocked[i])
            if matches == []:
                self.failed_or_blocked_notes_without_bug.append(i)
            else:
                for match in matches:
                    if match not in self.bugs_list:
                        self.bugs_list.append(match)
        if self.failed_or_blocked_notes_without_bug:
            print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            print('Данные заметки без каких-либо багов')
            for i in self.failed_or_blocked_notes_without_bug:
                print('---------------------------------------------------------------')
                print('ISSUE: ' + i)
                print(self.json_of_testcases_failed_or_blocked[i])
                print()


class CommunicateWithJira:
    @staticmethod
    def get_test_run_id_by_name(test_run_name):
        url = str(
            'http://jira.spiritcorp.com/rest/testy/3/runs?maxResult=-1&prefix=false&runName='
            + Code.replace_w_s(test_run_name)
        )
        response = requests.get(url, auth=('task', 'NIJ812rdf'))
        if '[]' == str(response.text):
            return False
        else:
            response_json = json.loads(str(response.text[1:-1]))
            response_id = response_json['id']
            return response_id

    @staticmethod
    def download_file(test_run_name, url, encoded_data):
        try:
            local_filename = test_run_name + ".xls"
            r = requests.post(url, stream=True, data=encoded_data, auth=('task', 'NIJ812rdf'), headers=headers)
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return local_filename
        except:
            print('Problem')
            return False

    @staticmethod
    def make_jql_query(list_of_bugs):
        for i in list_of_bugs:
            if jql_data['jql'] == '':
                jql_data['jql'] = 'issue = ' + i
            else:
                jql_data['jql'] = jql_data['jql'] + ' OR issue = ' + i
        url2 = str('http://jira/issues/?jql=' + Code.replace_w_s(jql_data['jql']))
        webbrowser.open_new_tab(url2)

    @staticmethod
    def put_result_to_jira(test_run_id, test_case_id, note):
        json_helper = JsonHelper()
        payload = json_helper.get_tc_json(note, 'task', note)
        url = str(
            'http://jira.spiritcorp.com/rest/testy/3/runs/' + str(test_run_id) + '/items/' + str(
                test_case_id))
        headers = {"content-type": "application/json"}
        requests.put(url, data=payload, headers=headers, auth=('task', 'NIJ812rdf'
                                                                       ''), verify=False)


class Code:
    @staticmethod
    def encode(message):
        url_params = urllib.parse.urlencode(message)
        url_params = url_params.replace('%27', '%22')
        url_params = url_params.replace('+%', '%')
        url_params = url_params.replace('+T', 't')
        url_params = url_params.replace('testRunId%22%3A+', 'testRunId%22%3A')
        return url_params

    @staticmethod
    def decode(message):
        params_dict = urllib.parse.parse_qsl(message)
        params = dict(params_dict)
        return params

    @staticmethod
    def replace_w_s(string):
        return string.replace(' ', '%20')


class JsonHelper:
    @staticmethod
    def get_tr_json(name, id_of_structure):
        return json.dumps({"name": name,
                           "structureId": int(id_of_structure)
                           })

    # JSON RESULTS
    @staticmethod
    def get_tc_json(result, author, note):
        # pass
        if result.lower().startswith('p'):
            return JsonHelper.get_tc_pass_json(author, note)
        # fail
        elif result.lower().startswith('f'):
            return JsonHelper.get_tc_fail_json(author, note)
        # block
        elif result.lower().startswith('b'):
            return JsonHelper.get_tc_block_json(author, note)
        # skip
        elif result.lower().startswith('s'):
            return JsonHelper.get_tc_skip_json(author, note)
        # none
        elif result.lower().startswith(''):
            return JsonHelper.get_tc_none_json(author, note)

    # pass json
    @staticmethod
    def get_tc_pass_json(author, note):
        return json.dumps({"status": {"id": 1,
                                      "priority": 1
                                      },
                           "authorKey": author,
                           "notes": note})

    # fail json
    @staticmethod
    def get_tc_fail_json(author, note):
        return json.dumps({"status": {"id": 3,
                                      "priority": -2
                                      },
                           "authorKey": author,
                           "notes": note})

    # block json
    @staticmethod
    def get_tc_block_json(author, note):
        return json.dumps({"status": {"id": 2,
                                      "priority": -1
                                      },
                           "authorKey": author,
                           "notes": note})

    # skip
    @staticmethod
    def get_tc_skip_json(author, note):
        return json.dumps({"status": {"id": 4,
                                      "priority": 2
                                      },
                           "authorKey": author,
                           "notes": note})

    # none
    @staticmethod
    def get_tc_none_json(author, note):
        return json.dumps({"status": {"id": 0,
                                      "priority": 0
                                      },
                           "authorKey": author,
                           "notes": note})

def startScr():
    decision = \
        input("Доступно на выбор несколько режимов работы скрипта. Выберите stalker:\n\n"
              "(Attention: Держите бекапы в одной папке со скриптом только если\n"
              "собираетесь их использовать, чтобы избежать недоразумений)\n\n"
              "1. Сделать BackUp тестового  прогона  в виде  xml  файла\n\n"
              "2. Открыть страницу со всеми багами упомянутыми в  Notes\n"
              "тестового прогона с информацией о неподкрепленных кейсах\n\n"
              "3. Восстановить тестовый прогон из BackUp\n"
              "Введите: ")
    if decision == '1':
        try:
            print('Для загрузки BackUp потребуется указать id структуры.')
            for i in range(1, len(structure_list) + 1):
                print('{}. {}'.format(str(i), structure_list[i - 1]))
            id = input('Введите номер из списка: ')
            data['forestSpec'] = '{"structureId": "%s"}' % str(structure_json[id])
            # print(data['forestSpec'])
            headers['Referer'] = 'http://jira.spiritcorp.com/secure/StructureBoard.jspa?s={}'.format(str(structure_json[id]))
            # print(headers['Referer'])

            dec = input('Показать существующие прогоны в данной структуре? ( yes \ no )')
            if dec.lower() == 'yes' or dec.lower() == 'да':
                url = "http://jira.spiritcorp.com/rest/testy/3/runs?structureId={}".format(str(structure_json[id]))
                headers2 = {"content-type": "application/json"}
                response = requests.get(url, headers=headers2, auth=('task', 'NIJ812rdf'), verify=False)
                json_data = json.loads(response.text)
                for i in range(0, len(json_data)):
                    print(str(i + 1) + '.', json_data[i]['name'])
                    structure_test_runs[str(i+1)] = json_data[i]['name']
                print(structure_test_runs)



            jira = JiraUtil(data)
            jira.structure_id = structure_json[id]
            CommunicateWithJira.download_file(jira.test_run_name, jira.url, jira.encoded_data)
            print('BackUp создан и находится в одной дирректории со скриптом!')
        except AttributeError:
            print('Не удалось выполнить загрузку из-за неправильного TestRun Name')
    elif decision == '2':
        try:
            print('Для загрузки BackUp потребуется указать id структуры.')
            for i in range(1, len(structure_list) + 1):
                print('{}. {}'.format(str(i), structure_list[i - 1]))
            id = input('Введите номер из списка: ')
            data['forestSpec'] = '{"structureId": "%s"}' % str(structure_json[id])
            # print(data['forestSpec'])
            headers['Referer'] = 'http://jira.spiritcorp.com/secure/StructureBoard.jspa?s={}'.format(
                str(structure_json[id]))
            # print(headers['Referer'])

            dec = input('Показать существующие прогоны в данной структуре? ( yes \ no )')
            if dec.lower() == 'yes' or dec.lower() == 'да':
                url = "http://jira.spiritcorp.com/rest/testy/3/runs?structureId={}".format(str(structure_json[id]))
                headers2 = {"content-type": "application/json"}
                response = requests.get(url, headers=headers2, auth=('task', 'NIJ812rdf'), verify=False)
                json_data = json.loads(response.text)
                for i in range(0, len(json_data)):
                    print(str(i + 1) + '.', json_data[i]['name'])
                    structure_test_runs[str(i+1)] = json_data[i]['name']
                print(structure_test_runs)
            jira = JiraUtil(data)
            CommunicateWithJira.download_file(jira.test_run_name, jira.url, jira.encoded_data)
            jira.analyze_xls()
            if jira.bugs_list:
                CommunicateWithJira.make_jql_query(jira.bugs_list)
            else:
                print("Страница не открылась, так баги в прогоне отсутствуют!")
                if jira.failed_or_blocked_notes_without_bug:
                    print("Проверьте наличие failed тест-кейсов без багов в notes\n"
                          "Они указаны в консоли сверху с подробностями")
                else:
                    print("У вас прогон либо весь зеленый, либо работа работа над ним еще не велась")

        except AttributeError:
            print('Не удалось выполнить загрузку из-за неправильного TestRun Name')
        except:
            print('Неизвестная ошибка')
    elif decision == '3':
        try:
            jira = JiraUtil(data)
            jira.analyze_xls()
            print('Началось восстановление данных в тестовом прогоне ' + jira.test_run_name + ': ')
            print('[', end='')
            limit = len(jira.json_of_testcases)
            a = 0
            for i in jira.json_of_testcases:
                a += 1
                CommunicateWithJira.put_result_to_jira(jira.test_run_id, i, jira.json_of_testcases[i])
                if (a % 6) == 0:
                    print('+', end='')
            print(']')
            print('Восстановление завершено')
        except:
            print('Проверьте наличие BackUp')
    elif decision.lower() == 'stalker':
        print('Короче, Тестер, я тебя спас и в благородство играть не буду: устроишь мне оплачиваемый отпуск\n'
              ' — и мы в расчете. Заодно посмотрим, как быстро у тебя башка после выходных прояснится. А по \n'
              'твоей теме постараюсь разузнать. Хрен его знает, на кой ляд тебе этот бэкап тест прогона \n'
              'сдался, но я в чужие дела не лезу, хочешь подстраховаться, значит есть за чем...')
    elif decision not in ['1', '2', '3', 'stalker']:
        print("Неверно выбран режим")


startScr()














