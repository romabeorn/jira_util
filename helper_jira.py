import datetime
import json
import multiprocessing
import os
import re
import sys
import urllib
import webbrowser
import xml.etree.ElementTree as Et
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests as req
import xlrd
import xmltodict

# import l

class Vars:
    """ Класс параметров для выполнения кода """

    def __init__(self):
        self.host = 'jira.spiritcorp.com'  # Хост JIRA
        self.login = 'task'  # Логин сервис-пользователя
        self.password = 'NIJ812rdf'  # Пароль сервис-пользователя
        self.protocol_d = 'http'  # протокол, на котором поддерживается JIRA
        self.PORT_NUMBER = 8000
        self.test_run = ''
        self.json_request_for_xml = {
            "forestSpec": '{"structureId": ""}',  # Обязательно указать ID структуры
            "viewSpec": {
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
                        "params": {}
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
                            "testRunId": 0
                        },
                        "csid": "#1"
                    },
                    {
                        "csid": "actions",
                        "key": "actions"
                    }
                ]
            },
            "expand": "10000"
        }
        self.jql_data = {'jql': '', 'decorator': None}
        self.backup_folder = 'backups'
        self.base_headers = {'content-type': 'application/json'}


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


class TestRun(Vars):
    def __init__(self, structure_id, structure_name):
        Vars.__init__(self)
        self.download_xml_headers = {
            'X-Atlassian-Token': 'no-check',
            'Host': f'{self.host}',
            'Origin': f'{self.protocol_d}://{self.host}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': f'{self.protocol_d}://{self.host}/secure/StructureBoard.jspa?s=',
            'Accept-Encoding': 'gzip, deflate',

        }
        self.structure_id = structure_id
        self.selected_structure_name = structure_name
        self.test_runs = None
        self.test_runs_list = []
        self.test_runs_json = {}
        self.selected_id = None  # Выбранный порядковый номер
        self.selected_test_run_id = None  # ID Выбранного прогона
        self.selected_test_run_name = None  # Название выбранного прогона
        self.create_tmp_dir_if_not_existed()
        self.selected_test_run_name_xls = None

    def update_download_xml_headers(self):
        """ После выбора структуры обновляем headers до актуального состояния """
        self.download_xml_headers['Referer'] = f'{self.protocol_d}://{self.host}' \
                                               f'/secure/StructureBoard.jspa?s={self.structure_id}'

    def get_structure_test_runs_from_jira(self):
        """
        Получаем список JSON прогонов вида
        {
          "id": 68,
          "self": "http://jira/rest/testy/3/runs/68",
          "structure": {
            "id": 3,
            "self": "http://jira/rest/structure/2.0/structure/3"
          },
          "name": "Test RUN №1"
        }
        """
        url = f'{self.protocol_d}://{self.host}/rest/testy/3/runs?structureId={self.structure_id}'
        response = req.get(url, headers=self.base_headers, auth=(self.login, self.password), verify=False)
        self.test_runs = json.loads(response.text)

    def order_gotten_test_runs(self):
        """ Упорядочиваем список полученных прогонов """
        self.test_runs = self.sort_json_test_runs(self.test_runs)
        for test_run in self.test_runs:
            self.test_runs_list.append(test_run['name'])
            self.test_runs_json[f'{len(self.test_runs_list)}'] = test_run['id']

    @staticmethod
    def sort_json_test_runs(test_runs):
        return sorted(test_runs, key=lambda k: list(map(int, re.compile('(\d+)').findall(k['name']))))

    def print_allowed_test_runs(self):
        """ Вывести доступные прогоны на экран """
        print(f'NUMBER OF TEST RUNS IN STRUCTURE: {len(self.test_runs_list)}')
        for order_id, name in enumerate(self.test_runs_list, 1):
            print(f'{order_id}. {name}')

    def get_test_run_name_by_order_id(self, order_id):
        """  Возвращает название прогона по порядковому номеру, выбранного пользователем """
        keys_list = list(self.test_runs_json.keys())
        if order_id in keys_list:
            return self.test_runs_list[int(order_id) - 1]
        else:
            raise ValueError('Selected ID doesn\'t exist in list')

    def get_test_run_id_by_order_id(self, order_id):
        """  Возвращает ID прогона по порядковому номеру, выбранного пользователем """
        keys_list = list(self.test_runs_json.keys())
        if order_id in keys_list:
            return self.test_runs_json[order_id]
        else:
            raise ValueError('Selected ID doesn\'t exist in list')

    @staticmethod
    def get_test_run_id_by_name(structure_id, structure_name, test_run_name):
        obj = TestRun(structure_id, structure_name)
        obj.get_structure_test_runs_from_jira()
        obj.order_gotten_test_runs()
        for order_id, name in enumerate(obj.test_runs_list, 1):
            if test_run_name[0] == name:
                return obj.test_runs_json[f'{order_id}']

    def setup_interactive_mode(self):
        """ Запуск интерактивного режима """
        try:
            self.get_structure_test_runs_from_jira()
            self.order_gotten_test_runs()
            self.print_allowed_test_runs()
            decision = input('Select Test Run. Enter ID: ')
            self.selected_id = decision
            self.selected_test_run_id = self.get_test_run_id_by_order_id(decision)
            self.selected_test_run_name = self.get_test_run_name_by_order_id(decision)
            print()
            print(f'Selected order ID - {self.selected_id}\n'
                  f'JIRA Test Run ID - {self.selected_test_run_id}\n'
                  f'Test Run Name - {self.selected_test_run_name}\n'
                  f'Structure ID - {self.structure_id}')
            print()
            return self.selected_id, self.selected_test_run_id, self.selected_test_run_name
        except ValueError as e:
            print(e)
            print('Please, try again')
            self.__init__(self.structure_id, self.selected_structure_name)
            return self.setup_interactive_mode()

    def download_test_run_xml_file(self):
        try:
            self.json_request_for_xml['viewSpec']['columns'][-2]['params']['testRunId'] = int(self.selected_test_run_id)
            self.json_request_for_xml['viewSpec']['columns'][-2]['name'] = self.selected_test_run_name
            self.json_request_for_xml['forestSpec'] = '{"structureId": "%s"}' % self.structure_id
            url = f'{self.protocol_d}://{self.host}/plugins/servlet/structure/excel HTTP/1.1'
            pattern_file_name = f'{self.selected_structure_name}. Test Run - {self.selected_test_run_name}.xls'
            local_filename = f'{self.backup_folder}/{pattern_file_name}'
            encoded_data = Code.encode(self.json_request_for_xml)
            response = req.post(url, stream=True, data=encoded_data, auth=(self.login, self.password),
                                headers=self.download_xml_headers)
            with open(local_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            self.selected_test_run_name_xls = pattern_file_name
            return local_filename
        except Exception as e:
            print(e)
            print('Error while Creating Backup')

    def create_tmp_dir_if_not_existed(self):
        if f'{self.backup_folder}' not in os.listdir(os.path.abspath('')):
            os.mkdir(f'{self.backup_folder}')

    @staticmethod
    def create_test_run(test_run_name, structure_id):
        base_headers = {'content-type': 'application/json',
                        'Referer': f'{Vars().protocol_d}://{Vars().host}/secure/StructureBoard.jspa?s='}
        json_data = {"name": "", "structureId": None}  # {"name":"VM 9.9.9.9","structureId":3}
        url = f'{Vars().protocol_d}://{Vars().host}/rest/testy/2/run'
        json_data['name'] = test_run_name
        json_data['structureId'] = int(structure_id)
        res = req.post(url, data=json.dumps(json_data), headers=base_headers, auth=(Vars().login, Vars().password),
                       verify=False)
        code = res.status_code
        if code == 201:
            print(f'Test Run {test_run_name} created')
        elif code == 400:
            print(f'{test_run_name} already exists or bad name has been selected')
        else:
            print(f'Error Creating Test Run: Status Code - {code}')

    @staticmethod
    def delete_test_run(test_run_id, _):
        base_headers = {'content-type': 'application/json'}
        json_data = {}
        url = f'{Vars().protocol_d}://{Vars().host}/rest/testy/2/run/{test_run_id}'
        res = req.delete(url, data=json.dumps(json_data), headers=base_headers, auth=(Vars().login, Vars().password),
                         verify=False)
        code = res.status_code
        if code == 204:
            print('Test Run Deleted')
        else:
            print('Error')


class StructureIDs(Vars):
    def __init__(self):
        Vars.__init__(self)
        self.content = {}  # Ответ сервера
        self.url = f'{self.protocol_d}://{self.host}/rest/structure/2.0/structure?withPermissions=true'
        self.structure_list = []  # Список названий структур ['Big Test', 'Test Android', ... ]
        self.structure_json = {}  # Список ID структур в JIRA {'1': '20', '2': '10', ... }
        self.selected_id = None  # Выбранный порядковый номер
        self.selected_structure_id = None  # ID Выбранной структуры
        self.selected_structure_name = None  # Название выбранной структуры

    def order_gotten_structures(self):
        """ Упорядочиваем полученные структуры по ID для возможности выбрать нужную структуру в интерактивном режиме """
        for structure in self.content['structureList']['structures']['structure']:
            self.structure_list.append(structure['name'])
            self.structure_json[f'{len(self.structure_list)}'] = structure['id']

    def get_structures_from_jira(self):
        """ Получаем ответ от сервера запросом с выбранной структурой """
        self.content = req.get(self.url, auth=(self.login, self.password)).content.decode('utf-8')
        return self.content

    def to_json(self):
        """ Форматируем ответ в JSON объект """
        self.content = json.dumps(xmltodict.parse(self.content), indent=4)
        self.content = json.loads(self.content)
        return self.content

    def get_content(self):
        """ Выводим переменную Content """
        print(self.content)

    def fast_order(self):
        """ Вся работа класса в один метод """
        self.get_structures_from_jira()
        self.to_json()
        self.order_gotten_structures()
        return self.structure_json

    def get_structure_name_by_order_id(self, order_id):
        """  Возвращает название структуры по порядковому номеру, выбранного пользователем """
        keys_list = list(self.structure_json.keys())
        if order_id in keys_list:
            return self.structure_list[int(order_id) - 1]
        else:
            raise ValueError('Selected ID doesn\'t exist in list')

    def get_structure_id_by_order_id(self, order_id):
        """  Возвращает ID структуры по порядковому номеру, выбранного пользователем """
        keys_list = list(self.structure_json.keys())
        if order_id in keys_list:
            return self.structure_json[order_id]
        else:
            raise ValueError('Selected ID doesn\'t exist in list')

    @staticmethod
    def get_structure_id_by_name(structure_name):
        obj = StructureIDs()
        obj.fast_order()
        for order_id, name in enumerate(obj.structure_list, 1):
            if structure_name[0] == name:
                return obj.structure_json[f'{order_id}']

    def print_allowed_strucutres(self):
        """ Вывести доступные структуры на экран """
        for order_id, name in enumerate(self.structure_list, 1):
            print(f'{order_id}. {name}')

    def setup_interactive_mode(self):
        """ Запуск интерактивного режима """
        try:
            self.fast_order()
            self.print_allowed_strucutres()
            decision = input('Select structure. Enter ID: ')
            self.selected_id = decision
            self.selected_structure_id = self.get_structure_id_by_order_id(decision)
            self.selected_structure_name = self.get_structure_name_by_order_id(decision)
            print()
            print(f'Selected order ID - {self.selected_id}\n'
                  f'JIRA structure ID - {self.selected_structure_id}\n'
                  f'Structure Name - {self.selected_structure_name}\n')
            print()
            return self.selected_id, self.selected_structure_id, self.selected_structure_name
        except ValueError as e:
            print(e)
            print('Please, try again')
            self.__init__()
            return self.setup_interactive_mode()


class BackUp:
    def __init__(self):
        self.xls_file_name = ''
        self.selected_id = None
        self.list_of_backups = list()
        self.update_list_of_backups()

    def update_list_of_backups(self):
        """ Обновляет список бэкапов в папке """
        self.list_of_backups = [name for name in os.listdir(os.path.abspath(f'{Vars().backup_folder}')) if
                                name.endswith('.xls')]

    def amount_of_backups(self):
        """ Возвращает и печатает кол-во бэкапов в папке """
        print(f'NUMBER OF BACKUPS IN FOLDER: {len(self.list_of_backups)}')
        return len(self.list_of_backups)

    def print_backups(self):
        """ Печатает пронумерованный списко бэкапов. Возвращает их список """
        self.update_list_of_backups()
        self.enumerate_backups(self.list_of_backups)
        return self.list_of_backups

    @staticmethod
    def enumerate_backups(list_of_backups):
        """ Нумерует и выводит список """
        for order_id, name in enumerate(list_of_backups, 1):
            print(f'{order_id}. {name}')

    def get_backup_name_by_order_id(self, order_id):
        order_id = int(order_id)
        if (order_id > 0) and (order_id <= len(self.list_of_backups)):
            return self.list_of_backups[order_id - 1]
        else:
            raise ValueError

    def print(self):
        print(f'\nBackUp Folder: {Vars().backup_folder}')
        print(f'Selected BackUp: {self.xls_file_name}')
        print(f'Selected ID: {self.selected_id}\n')

    def select_backup_file(self, backup_name=None):
        """ Запоминаем выбранный бэкап """
        try:
            if backup_name is None:
                self.amount_of_backups()
                self.print_backups()
                decision = input('Select backup from list: ')
                self.selected_id = decision
                self.xls_file_name = self.get_backup_name_by_order_id(decision)
                durak_proverka = input('WARNING!  Are you  sure with  decision?\n'
                                       'Restore will erase entire previous data\n'
                                       'of Test Run. (yes/no): ')
                if durak_proverka.lower() != 'yes':
                    self.select_backup_file()

            else:
                self.xls_file_name = backup_name
        except FileNotFoundError:
            print('Folder with backups doesn\'t exist')

        except ValueError:
            print('Selected ID is not in the list')
            self.select_backup_file()


class BackUpAnalyzer(BackUp):
    def __init__(self):
        BackUp.__init__(self)
        self.json_of_testcases_failed_or_blocked = {}
        self.json_of_testcases = {}
        self.bugs_list = list()
        self.failed_or_blocked_notes_without_bug = list()

    def analyze_xls(self, log=True):
        workbook = xlrd.open_workbook(f'{Vars().backup_folder}/{self.xls_file_name}')
        sheet = workbook.sheet_by_index(0)
        self.get_json_of_testcases(sheet.col_values(0), sheet.col_values(5))
        self.get_json_of_testcases_failed_or_blocked()
        self.get_list_of_bugs_in_notes(log=log)
        return self.bugs_list

    def get_json_of_testcases(self, keys, stat):
        """ Возвращает JSON вида {'TL-94': 'PASSED (Ivan Ivanov)\ncomment', ... """
        for i in range(1, len(keys)):
            if keys[i] != '':
                self.json_of_testcases[keys[i]] = stat[i]

    def get_json_of_testcases_failed_or_blocked(self):
        """ Возвращает JSON вида {'TL-94': 'FAILED (Ivan Ivanov)\ncomment', ... """
        for i in self.json_of_testcases:
            if self.json_of_testcases[i].startswith('FAILED') or self.json_of_testcases[i].startswith('BLOCKED'):
                self.json_of_testcases_failed_or_blocked[i] = self.json_of_testcases[i]

    def get_list_of_bugs_in_notes(self, log=True):
        res = req.get('http://jira.spiritcorp.com/rest/api/2/project', auth=((Vars().login, Vars().password)),
                      verify=False)
        projects = json.loads(res.text)
        projects_keys = [i["key"] for i in projects]
        a = ''
        for i in projects_keys:
            a += f'{i}|'
        pattern = '({})+-\d+'.format(a[:-1])

        for i in self.json_of_testcases_failed_or_blocked:
            matches = []
            matches_re = re.finditer(pattern, json.dumps(self.json_of_testcases_failed_or_blocked[i]), re.MULTILINE)
            for match in matches_re:
                matches.append((match.group()))
            if log:
                print(matches)
            if not matches:
                self.failed_or_blocked_notes_without_bug.append(i)
            else:
                for match in matches:
                    if match not in self.bugs_list:
                        self.bugs_list.append(match)
        if log:
            if self.failed_or_blocked_notes_without_bug:
                print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                print('These notes are without any bug')
                for i in self.failed_or_blocked_notes_without_bug:
                    print('---------------------------------------------------------------')
                    print(f'ISSUE: {i}')
                    print(f'{self.json_of_testcases_failed_or_blocked[i]}\n')
            else:
                print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                print('Every note has a bug. Cool Work!')
                print('---------------------------------------------------------------')


class JiraUtil(Vars):
    def make_jql_query(self, list_of_bugs):
        issues_str = ''
        for i in list_of_bugs:
            issues_str += f'{i}, '
        self.jql_data["jql"] = f'{issues_str[:-2]}'
        url = f'http://{self.host}/issues/?jql=issue in ({self.jql_data["jql"]}) ORDER BY priority DESC'
        webbrowser.open_new_tab(url)

    def put_result_to_jira(self, result, note, test_run_id, tc_id):
        payload = JsonHelper().get_tc_json(result, self.login, note)
        url = f'http://{self.host}/rest/testy/3/runs/{test_run_id}/items/{tc_id}'
        req.put(url, data=payload, headers=self.base_headers, auth=(str(self.login), str(self.password)), verify=False)

    def skip_results(self, test_run_id):
        now = datetime.datetime.now()
        skip_list = JsonHelper.get_skip_list()
        print('MAP FOR SKIPPING IS LOADED...\n')
        for tc_id in skip_list:
            print(tc_id)
            self.put_result_to_jira('skip',
                                    f'{tc_id}\nskipped\n{now.strftime("%Y-%m-%d %H:%M:%S")}',
                                    test_run_id,
                                    tc_id, )
            print(f'{tc_id} skipped')


class JsonHelper:
    @staticmethod
    def get_tr_json(name, id_of_structure):
        return json.dumps({'name': name,
                           'structureId': int(id_of_structure)
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
        elif result.lower().startswith('n'):
            return JsonHelper.get_tc_none_json(author, note)

    # pass json
    @staticmethod
    def get_tc_pass_json(author, note):
        return json.dumps({'status': {'id': 1,
                                      'priority': 1
                                      },
                           'authorKey': author,
                           'notes': note})

    # fail json
    @staticmethod
    def get_tc_fail_json(author, note):
        return json.dumps({'status': {'id': 3,
                                      'priority': -2
                                      },
                           'authorKey': author,
                           'notes': note})

    # block json
    @staticmethod
    def get_tc_block_json(author, note):
        return json.dumps({'status': {'id': 2,
                                      'priority': -1
                                      },
                           'authorKey': author,
                           'notes': note})

    # skip
    @staticmethod
    def get_tc_skip_json(author, note):
        return json.dumps({'status': {'id': 4,
                                      'priority': 2
                                      },
                           'authorKey': author,
                           'notes': note})

    # none
    @staticmethod
    def get_tc_none_json(author, note):
        return json.dumps({'status': {'id': 0,
                                      'priority': 0
                                      },
                           'authorKey': author,
                           'notes': note})

    # @staticmethod
    # def get_map_json():
    #     with open('map_test.json', 'r') as f:
    #         return json.load(f)[l.l['jira.testrun.structure.id']]['tests_map']
    #
    # @staticmethod
    # def get_skip_list():
    #     with open('map_test.json', 'r') as f:
    #         return json.load(f)[l.l['jira.testrun.structure.id']]['skip']


# print(JsonHelper().get_tc_json('Hailed','Roman', 'Note'))


# class helper
class XmlHelper:

    # Создает дирректорию test run в папке 'reports'

    @staticmethod
    def create_test_run_dir():
        path = os.path.abspath('reports/' + Vars().test_run)
        if not os.path.exists(path):
            os.mkdir(path)
        return True

    # Возвращает список экземляров класса XmlResult, содержащих имя XML файла c .xml и резульаь теста

    def get_results(self):
        list_of_xml_files = list()
        list_of_xml_results = list()
        for file in os.listdir('reports/'):
            if file.endswith('.xml'):
                list_of_xml_files.append(file)
        for xml_file in list_of_xml_files:
            list_of_xml_results.append(XmlResult(xml_file[:-4], self.get_result_of_xml_file(xml_file)))
        return list_of_xml_results
        # .sort(key=lambda x: x.name)

    # Возвращает результат теста из XML файла в виде строки

    @staticmethod
    def get_result_of_xml_file(xml_file_name):
        try:
            tree = Et.parse('reports/' + xml_file_name)
        except FileNotFoundError:
            print('XML File ' + xml_file_name + ' doesn\'t exist')
            return 'none'
        else:
            root = tree.getroot()
            return root[0].text


# Класс служит для создания экземляров, содержащих имя XML файла [vm_group__id_name___time.xml]
# в папке 'reports' и результат исолнения теста [passed / failed]. В методе get_result() класса
# XmlHelper создается список экземляров XmlResult класса

class XmlResult:
    def __init__(self, name, result):
        self.name = name
        self.result = result

    def __str__(self):
        return self.name + ' ' + str(self.result)

    # Возвращает имя xml файла с .xml на конце
    def get_name(self):
        return self.name

    # Возвращает строку [passed / failed]
    def get_result(self):
        return self.result

    # Переносит все лог-файлы из reports в папку с test run
    # def move_results_to_dir(self):
    #     for file in os.listdir('reports/'):
    #         if file.startswith(self.name):  # if pattern
    #             if file.endswith('.xml'):
    #                 os.rename('reports/' + file, 'reports/' + l.l['jira.testrun.name'] + '/' + file)
    #             elif file.endswith('.mp4'):
    #                 os.rename('reports/' + file, 'reports/' + l.l['jira.testrun.name'] + '/' + file)
    #             elif file.endswith('.png'):
    #                 os.rename('reports/' + file, 'reports/' + l.l['jira.testrun.name'] + '/' + file)


class PlotTestRuns(TestRun):
    def __init__(self, structure_id, structure_name):
        TestRun.__init__(self, structure_id, structure_name)
        self.selected_mode_of_plotting = ''
        self.range_first_test_run = ''
        self.range_last_test_run = ''
        self.selective_selected_test_run = []

    @staticmethod
    def accept_values(value, test_runs_list):
        if value.isdecimal():
            if int(value) in range(1, len(test_runs_list) + 1):
                return True
            else:
                return False
        else:
            return False

    def get_test_run_id_from_test_runs_json(self, selected_test_runs):
        return [f'{self.test_runs_json[str(i)]}' for i in selected_test_runs]

    @staticmethod
    def get_info_about_issue(issue_id):
        res = req.get(f'{Vars().protocol_d}://{Vars().host}/rest/api/2/issue/{issue_id}', auth=((Vars().login,Vars().password)))
        res = json.loads(res.text)
        # print(json.dumps(res))
        return {
            "name": res['key'],
            "summary": res['fields']['summary'],
            "description": res['fields']['description'],
            "issuetype": res['fields']['issuetype']['name'],
            "status": res['fields']['status']['name'],
            "statusId": res['fields']['status']['id'],
            "priority": res['fields']['priority']['name'],
            "priorityId": res['fields']['priority']['id'],
            "creator": res['fields']['creator']['displayName'],
            "assignee": res['fields']['assignee']['displayName']
        }

    @staticmethod
    def dump_reverted_massive(bugs_array, test_run_and_bug_tuples, selected_test_runs_range):
        lst = []
        for id, bug in enumerate(bugs_array, 1):
            json_mas = {}
            json_mas['id'] = id
            json_mas['bugName'] = bug
            json_mas['versions'] = []
            json_mas['issueProps'] = PlotTestRuns.get_info_about_issue(bug)
            for run in test_run_and_bug_tuples:
                if bug in run[1]:
                    json_mas['versions'].append({
                        'name': run[0],
                        'visible': True
                    })
                else:
                    json_mas['versions'].append({
                        'name': run[0],
                        'visible': False
                    })
            lst.append(json_mas)
            lst.sort(key=lambda s: s['issueProps']['priorityId'], reverse=True)
            for id, bug in enumerate(lst, 1):
                lst[id-1]['id'] = id

        lst = {"Labels": selected_test_runs_range,
               "BigData": lst}
        # print(lst)
        with open('plot/bigData.json', 'w') as f:
            f.write(json.dumps(lst, indent=4))

        return lst

    @staticmethod
    def f():
        server = HTTPServer(('', Vars().PORT_NUMBER), myHandler)
        server.serve_forever()

    @staticmethod
    def input_ordered_ids_of_set(test_runs_list):
        massive = set()
        print('Type identifiers of Test Runs\'. When finish print "ok"')
        while True:
            run = input(f'{len(massive) + 1}: ')
            if run == 'ok':
                break
            if PlotTestRuns.accept_values(run, test_runs_list):
                massive.add(run)
            print(massive)
        massive = list(map(str, sorted([int(i) for i in massive])))
        return massive

    def get_array_of_test_runs_and_bugs_there(self, jira_test_run_ids):
        print(jira_test_run_ids)
        global_list_of_bugs_with_run = list()
        bugs_array = set()
        for id, test_run_id in enumerate(jira_test_run_ids):
            print(id)
            local_list_of_bugs = list()
            test_run_inter_active_mode = TestRun(self.structure_id, self.selected_structure_name)
            test_run_inter_active_mode.selected_test_run_id = test_run_id
            test_run_inter_active_mode.selected_test_run_name = self.selected_test_runs_range[id]
            test_run_inter_active_mode.download_test_run_xml_file()
            backup = BackUpAnalyzer()
            sys.stdout.write('.')
            sys.stdout.flush()
            backup.select_backup_file(test_run_inter_active_mode.selected_test_run_name_xls)
            for i in backup.analyze_xls(log=False):
                local_list_of_bugs.append(i)
                bugs_array.add(i)
            global_list_of_bugs_with_run.append(
                (test_run_inter_active_mode.selected_test_run_name, local_list_of_bugs))
        return bugs_array, global_list_of_bugs_with_run

    def setup_plot_interactive_mode(self):
        mode = input('\nSelect mode of plotting\n'
                     '1. Range mode\n'
                     '2. Selective mode\n'
                     'Enter: ')
        try:
            self.selected_mode_of_plotting = mode
            if mode == '1':
                first_run = input('Enter id of the first  Test Run: ')
                second_run = input('Enter id of the second Test Run: ')
                if self.accept_values(first_run, self.test_runs_list) and self.accept_values(second_run, self.test_runs_list):
                    if int(first_run) > int(second_run):
                        first_run, second_run = second_run, first_run
                    range_runs = range(int(first_run), int(second_run) + 1)  # Список номеров между выбранными прогонами

                    self.selected_test_runs_range = [self.test_runs_list[int(i) - 1] for i in range_runs]  # Список названий выбранных прогонов

                    self.jira_test_run_ids = self.get_test_run_id_from_test_runs_json(range_runs)  # Список JIRA ids прогонов

                    self.bugs_array, self.test_run_and_bugs_tuples = self.get_array_of_test_runs_and_bugs_there(self.jira_test_run_ids)

                    # Меняем вид в котором прогон состоял из багов на вид, где баг состоит из прогонов в которых он есть и делаем дамп в файл
                    # bugs_array - множество багов,
                    # test_run_and_bugs_tuples - список кортежей (прогон - спиок багов),
                    # selected_test_runs_range - cписок названий выбранных прогонов
                    PlotTestRuns.dump_reverted_massive(self.bugs_array,
                                                       self.test_run_and_bugs_tuples,
                                                       self.selected_test_runs_range)
                else:
                    raise ValueError

            elif mode == '2':  # Selective mode
                range_of_runs = PlotTestRuns.input_ordered_ids_of_set(self.test_runs_list)
                print(range_of_runs)  # ['2', '4', '8', '13', '21', '30', '31']
                selected_test_runs = [self.test_runs_list[int(i)-1] for i in range_of_runs]  # Список названий выбранных прогонов
                jira_test_run_ids = self.get_test_run_id_from_test_runs_json(range_of_runs)  # Список id прогонов JIRA
                print(jira_test_run_ids)  # ['17', '27', '61', '78', '97', '205', '211']
                print(selected_test_runs) # ['VM 6.2.0.390 ', 'VM 6.2.0.411', 'VM 6.3.0.12', 'VM 6.3.0.47', 'VM 6.3.0.77', 'VM 6.3.3.35', 'VM 6.3.3.37']
                self.selected_test_runs_range = [self.test_runs_list[int(i) - 1] for i in
                                                 range_of_runs]  # Список названий выбранных прогонов

                self.jira_test_run_ids = self.get_test_run_id_from_test_runs_json(
                    range_of_runs)  # Список JIRA ids прогонов

                self.bugs_array, self.test_run_and_bugs_tuples = self.get_array_of_test_runs_and_bugs_there(
                    self.jira_test_run_ids)

                # Меняем вид в котором прогон состоял из багов на вид, где баг состоит из прогонов в которых он есть и делаем дамп в файл
                # bugs_array - множество багов,
                # test_run_and_bugs_tuples - список кортежей (прогон - спиок багов),
                # selected_test_runs_range - cписок названий выбранных прогонов
                PlotTestRuns.dump_reverted_massive(self.bugs_array,
                                                   self.test_run_and_bugs_tuples,
                                                   self.selected_test_runs_range)

            else:
                print('Wrong mode. Exiting')
                return self.setup_plot_interactive_mode()
        except ValueError:
            print('Wrong selection try again')
            return self.setup_plot_interactive_mode()
        except:
            print('Error')


class myHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        self.send_response(200)
        self.end_headers()
        if self.path == '/plot/index.html':
            self.send_header('Content-type', 'text/html')
            with open(os.path.abspath('plot/index.html')) as f:
                html = f.read()
            self.wfile.write(html.encode())

        if self.path == '/plot/bigData.json':
            self.send_header('Content-type', 'application/json')
            with open(os.path.abspath('plot/bigData.json')) as f:
                json = f.read()
            self.wfile.write(json.encode())

        if self.path == '/plot/app.js':
            self.send_header('Content-type', 'application/javascript')
            with open(os.path.abspath('plot/app.js')) as f:
                js = f.read()
            self.wfile.write(js.encode())

        if self.path == '/plot/style.css':
            self.send_header('Content-type', 'application/x-css')
            with open('D:/update_remove_install3/plot/style.css') as f:
                css = f.read().encode('utf-8')
                print(css)
            self.wfile.write(css)

        return


class JiraHelper:
    @staticmethod
    def main():
        decision = \
            input('There are 4 modes of script. Select one of them: \n\n'
                  '(Attention: Keep backups in one directory with script if you are dealing with it only!)\n\n'
                  '1. Create backup of Test Run (.xml format file)\n\n'
                  '2. Open Jira search page with bugs in Test Run\'s notes\n'
                  'with information in console about bugs not spotted in notes\n\n'
                  '3. Restore Test Run\'s Backup\n\n'
                  '4. Fill into JIRA results of Automation Test Run\n\n'
                  '5. Create Test Run in JIRA Structure\n\n'
                  '6. Delete Test Run in JIRA Structure\n\n'
                  '7. Draw a plot of bag statuses of JIRA structure\n'
                  'Enter: ')

        if decision == '1':
            struct_inter_active_mode = StructureIDs()
            struct_inter_active_mode.setup_interactive_mode()
            test_run_inter_active_mode = TestRun(struct_inter_active_mode.selected_structure_id,
                                                 struct_inter_active_mode.selected_structure_name)
            test_run_inter_active_mode.setup_interactive_mode()
            test_run_inter_active_mode.download_test_run_xml_file()
            print(f'BackUp has been created and located in same directory with script!')

        elif decision == '2':
            struct_inter_active_mode = StructureIDs()
            struct_inter_active_mode.setup_interactive_mode()
            test_run_inter_active_mode = TestRun(struct_inter_active_mode.selected_structure_id,
                                                 struct_inter_active_mode.selected_structure_name)
            test_run_inter_active_mode.setup_interactive_mode()
            test_run_inter_active_mode.download_test_run_xml_file()
            backup = BackUpAnalyzer()
            backup.select_backup_file(test_run_inter_active_mode.selected_test_run_name_xls)
            backup.analyze_xls()
            if backup.bugs_list:
                JiraUtil().make_jql_query(backup.bugs_list)
            else:
                print('Page has not been opened because bugs don\'t exist')
                if backup.failed_or_blocked_notes_without_bug:
                    print('Check failed testcases in Test Run\n'
                          'They are located upper in console')
                else:
                    print('Test Run is completely green or work hasn\'t been started')

        elif decision == '3':
            backup = BackUpAnalyzer()
            backup.select_backup_file()
            backup.analyze_xls()
            a = 0
            jira_test_run_name = re.compile('Test Run - (.+)\.xls')
            jira_structure_name = re.compile('(.+)\. Test Run - ')
            jira_test_run_name = jira_test_run_name.findall(backup.xls_file_name)
            jira_structure_name = jira_structure_name.findall(backup.xls_file_name)
            structure_id = StructureIDs().get_structure_id_by_name(jira_structure_name)
            test_run_id = TestRun.get_test_run_id_by_name(structure_id, jira_structure_name, jira_test_run_name)

            for key in backup.json_of_testcases:
                a += 1
                JiraUtil().put_result_to_jira(backup.json_of_testcases[key], backup.json_of_testcases[key], test_run_id,
                                              key)
                if (a % 6) == 0:
                    print('+', end='')
            print('Restore completed')

        elif decision == '4':
            # test_run_id = TestRun.get_test_run_id_by_name(structure_id, jira_structure_name, jira_test_run_name)
            # JiraUtil().skip_results('TEST')
            print('Developing...')

        elif decision == '5':
            _, structure_id, structure_name = StructureIDs().setup_interactive_mode()
            test_run_inter_active_mode = TestRun(structure_id, structure_name)
            test_run_inter_active_mode.get_structure_test_runs_from_jira()
            test_run_inter_active_mode.order_gotten_test_runs()
            test_run_inter_active_mode.print_allowed_test_runs()
            test_run = input('Enter Test Run\'s name (check it\'s presence in the list!): ')
            test_run_inter_active_mode.create_test_run(test_run, structure_id)

        elif decision == '6':
            _, structure_id, structure_name = StructureIDs().setup_interactive_mode()
            durak = ''
            selected_test_run_id = ''
            while durak != 'yes':
                _, selected_test_run_id, _ = TestRun(structure_id, structure_name).setup_interactive_mode()
                durak = input('WARNING!  Are you  sure with  decision?\n'
                              'Entire data will  be  erased  (yes/no): ')
            TestRun.delete_test_run(selected_test_run_id, structure_id)

        elif decision == '7':
            print('Developing...')
            _, structure_id, structure_name = StructureIDs().setup_interactive_mode()
            run = PlotTestRuns(structure_id, structure_name)
            run.get_structure_test_runs_from_jira()
            run.order_gotten_test_runs()
            run.print_allowed_test_runs()
            run.setup_plot_interactive_mode()
            p = multiprocessing.Process(target=PlotTestRuns.f, args=())
            p.start()
            webbrowser.open_new_tab('http://localhost:8000/plot/index.html')
            while True:
                if input() == 'exit':
                    p.terminate()
                    break


        elif decision == '8':
            print('OUT')
            struct_inter_active_mode = StructureIDs()
            struct_inter_active_mode.setup_interactive_mode()
            test_run_inter_active_mode = TestRun(struct_inter_active_mode.selected_structure_id,
                                                 struct_inter_active_mode.selected_structure_name)
            test_run_inter_active_mode.get_structure_test_runs_from_jira()
            test_run_inter_active_mode.order_gotten_test_runs()

        elif decision.lower() == 'stalker':
            print('Короче, Тестер, я тебя спас и в благородство играть не буду: устроишь мне оплачиваемый отпуск\n'
                  ' — и мы в расчете. Заодно посмотрим, как быстро у тебя башка после выходных прояснится. А по \n'
                  'твоей теме постараюсь разузнать. Хрен его знает, на кой ляд тебе этот бэкап тест прогона \n'
                  'сдался, но я в чужие дела не лезу, хочешь подстраховаться, значит есть за чем...')

        elif decision:
            print('Wrong mode')


if '__main__' == __name__:
    try:
        req.get(f'{Vars().protocol_d}://{Vars().host}', auth=((Vars().login, Vars().password)))
        JiraHelper.main()
    except Exception as e:
        print(f'Connection to {Vars().host} failed')
        exit()
    # issue = 'VM-10463'
    # res = req.get(f'{Vars().protocol_d}://{Vars().host}/rest/api/2/issue/{issue}', auth=((Vars().login, Vars().password)))
    # res = json.loads(res.text)
    # print(res['fields']['status']['id'])
    # print(PlotTestRuns.get_info_about_issue('TL-1638'))
    # res = req.get(f'{Vars().protocol_d}://{Vars().host}/rest/api/2/priority', auth=((Vars().login, Vars().password)))
    # print(res.text)
    # import sys
#  Closed 6
#
