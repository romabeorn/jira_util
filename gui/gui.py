from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.config import Config
from kivy.core.image import Image as CoreImage
from kivy.graphics import Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.factory import Factory
from kivy.clock import Clock
from helper_jira_gui import *

WIDTH = 1366
HEIGHT = 768
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'width', f'{WIDTH}')
Config.set('graphics', 'height', f'{HEIGHT}')

class Helper:
    @staticmethod
    def colorer():
        modes = [
            'Backup TR',
            'Analyze TR',
            'Restore TR',
            'Create TR',
            'Delete TR',
            'Draw a PLOT of Structure TR'
        ]
        for i in range(0, len(modes)):
            yield i, modes[i].upper(), .68, .53, .60, .60

    @staticmethod
    def draw_background(widget):
        widget.canvas.before.clear()
        with widget.canvas.before:
            texture = CoreImage("data/logo/image.png").texture
            texture.wrap = 'repeat'
            Rectangle(pos=(0, 0), size=(WIDTH, HEIGHT + 20), texture=texture)

class MainMenu():
    def __init__(self):
        self.functions = [self.make_backup, self.make_backup_analyze, self.func, self.func, self.func, self.func, self.func]
        self.mode = ''
        self.count = 0

    def list_structure_items(self, items, func):
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=[200, 100, 30, 19])
        layout.bind(minimum_height=layout.setter('height'))
        layout.add_widget(Label(text='SELECT ITEM', font_size=25, size_hint_y=None, height=40))
        for id, i in enumerate(items):
            self.btn = Button(text=str(i), size_hint_y=None, height=40, background_color=[.68, .53, .60, .60], background_down='', color=[1, 1, 1, 1],
                              on_press=lambda i: func(i.text))
            layout.add_widget(self.btn)

        root = ScrollView(size_hint=(1, None), size=(WIDTH, HEIGHT))
        root.add_widget(layout)
        return root

    def make_backup_download(self, param):
        self.tr_mode.selected_test_run_name = param
        # print(type(self.tr_mode.structure_id), type(self.tr_mode.selected_structure_name), type(param))
        self.tr_mode.selected_test_run_id = self.tr_mode.get_test_run_id_by_name(self.tr_mode.structure_id, self.tr_mode.selected_structure_name, param)
        print(self.tr_mode.selected_test_run_id)
        self.tr_mode.download_test_run_xml_file()
        if self.mode == 'analyze':
            backup = BackUpAnalyzer()
            backup.select_backup_file(self.tr_mode.selected_test_run_name_xls)
            print(self.tr_mode.selected_test_run_name_xls)
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

    def make_backup_analyze(self, param):
        self.mode = 'analyze'
        self.struct_mode = StructureIDs()
        self.struct_mode.fast_order()
        try:
            self.bl.remove_widget(self.lst)
        except:
            pass
        self.lst = self.list_structure_items(self.struct_mode.structure_list, self.make_backup_tr)
        self.bl.add_widget(self.lst)


    def make_backup_tr(self, decision):
        order_id = self.struct_mode.get_structure_order_id_by_name(decision)
        selected_structure_id = self.struct_mode.get_structure_id_by_order_id(str(order_id + 1))
        self.tr_mode = TestRun(selected_structure_id,
                               decision)
        self.tr_mode.get_structure_test_runs_from_jira()
        self.tr_mode.order_gotten_test_runs()
        try:
            self.bl.remove_widget(self.lst)
        except:
            pass
        self.lst = self.list_structure_items(self.tr_mode.test_runs_list, self.make_backup_download)
        self.bl.add_widget(self.lst)

    def make_backup(self, param):
        self.mode = 'backup'
        self.struct_mode = StructureIDs()
        self.struct_mode.fast_order()
        try:
            self.bl.remove_widget(self.lst)
        except:
            pass
        self.lst = self.list_structure_items(self.struct_mode.structure_list, self.make_backup_tr)
        self.bl.add_widget(self.lst)



    def func(self):
        pass

    def wrap_check_connection(self, dt):
        try:
            req.get(f'{Vars().protocol_d}://{Vars().host}', auth=((Vars().login, Vars().password)))

            if self.once_checked:
                self.once_checked = False
                self.bl.clear_widgets()
                self.gl.add_widget(
                    Label(text='SELECT MODE TO CONTINUE', font_size=25, size_hint=[None, None],
                          size=(WIDTH * 2 / 5 - 40, 200)))
                for id, text, r, g, b, a in Helper.colorer():
                    self.gl.add_widget(
                        Button(text=text, background_color=[r, g, b, a], background_normal='', color=[1, 1, 1, 1],
                               font_size=17,
                               bold='1', on_press=self.functions[id]))
                self.bl.add_widget(self.gl)
            return True
        except Exception:
            self.bl.clear_widgets()
            self.gl.clear_widgets()
            self.bl.add_widget(Label(text=f'Connection to {Vars().host} failed', font_size=40, bold='l'))
            self.once_checked = True

    def main(self):
        self.once_checked = True
        self.bl = GridLayout(cols=2)
        self.gl = GridLayout(cols=1, spacing=5, padding=20, size_hint=[None, None],
                             size=(WIDTH * 2 / 5, HEIGHT))
        Helper.draw_background(self.bl)
        Helper.draw_background(self.gl)
        Clock.schedule_interval(self.wrap_check_connection, 2)
        return self.bl

class ST_ToolApp(App):
    def build(self):

        return MainMenu().main()


if "__main__" == __name__:
    ST_ToolApp().run()
    # help(Button)

