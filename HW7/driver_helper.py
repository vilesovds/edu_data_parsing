from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class ExtChrome(webdriver.Chrome):
    def __init__(self, *args, **kwargs):
        super(ExtChrome, self).__init__(*args, **kwargs)

    def open_in_new_tab(self, new_url):
        self.execute_script("window.open('');")
        self.switch_to.window(self.window_handles[-1])
        self.get(new_url)

    def close_but_index(self, index):
        wh = self.window_handles
        wh.remove(self.window_handles[index])
        for w in wh:
            self.switch_to.window(w)
            self.close()
        # switch back
        self.switch_to.window(self.window_handles[0])


def get_driver(driver_path, window_size=None, headless=False, user_agent=None):
    # options
    options = webdriver.ChromeOptions()
    options.headless = headless
    # user-agent
    if user_agent:
        options.add_argument(user_agent)
    else:
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/88.0.4324.182 Safari/537.36")

    if window_size:
        options.add_argument(f'window-size={window_size[0]},{window_size[1]}')
    options.add_argument("start-maximized")
    # disable webdriver mode
    # options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "eager"  # interactive

    return ExtChrome(desired_capabilities=caps,
                     executable_path=driver_path,
                     options=options)
