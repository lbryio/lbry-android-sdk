# going forward, this should match sdk version
__version__ = "0.102.0"

class ServiceApp(App):
    def build(self):
        from jnius import autoclass

        Intent = autoclass('android.content.Intent')
        LbrynetService = autoclass('io.lbry.lbrysdk.LbrynetService')

if __name__ == '__main__':
    ServiceApp().run()
