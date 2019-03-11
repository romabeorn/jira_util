from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout

from kivy.uix.button import Button
from kivy.uix.label import Label

class MainMenu():
    def colorer(self):
        a = 1/7
        text = [
            '1. Create backup of Test Run (.xml format file)',
            '2. Open Jira search page with bugs in Test Run\'s notes\n'
                                  'with information in console about bugs not spotted in notes',
            '3. Restore Test Run\'s Backup',
            '4. Fill into JIRA results of Automation Test Run',
            '5. Create Test Run in JIRA Structure',
            '6. Delete Test Run in JIRA Structure',
            '7. Draw a plot of bag statuses of JIRA structure'
        ]
        # [.48, .78, .91, 1]
        for i in range(0, len(text)):
            yield text[i], .48, .78, .90, 1 - i/(len(text)+1)

    def main(self):
        bl = BoxLayout(orientation='vertical', padding=50, spacing=20)
        for text, r, g, b, a in self.colorer():
            bl.add_widget(Button(text=text,
                                 background_color=[r, g, b, a],
                                 background_normal='',))

        return bl


class ExampleApp(App):
    def build(self):
        return MainMenu().main()


if "__main__" == __name__:
    ExampleApp().run()
