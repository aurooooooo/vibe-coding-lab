import time
import os
from selenium import webdriver
# --- 【核心修改】切换为 Chrome 组件 ---
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# ------------------------------------
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime, date
from selenium.common.exceptions import ElementClickInterceptedException


def calculate_days_from_today(target_date_str, date_format="%Y-%m-%d"):
    try:
        today = date.today()
        target_datetime = datetime.strptime(target_date_str, date_format)
        target_date = target_datetime.date()
        delta_days = abs((target_date - today).days)
        return delta_days
    except ValueError as e:
        print(f"日期格式错误：{e}")
        return None


# ================= 配置区域 =================
# 1. Chrome 驱动路径 (你之前提供的路径)
DRIVER_PATH = r"D:\chromeDriver\chromedriver.exe"

# 2. 用户数据路径 (改为 Chrome 专用文件夹，防止冲突)
current_dir = os.path.dirname(os.path.abspath(__file__))
USER_DATA_PATH = os.path.join(current_dir, "AutomationProfile_Chrome")

# 3. 多用户配置列表
TARGET_USERS = [
    {
        "id": "xxx【这里填写抖音号】",
        "name": "xxx 【这里填写抖音名称，推荐给目标备注后，填写备注名】",
        "date": "2022-10-26  【这里设置一个日期】",
        "template": "宝宝，今天是爱你的{days}天 【这里自动识别{days}并计算天数】"
    },
    {
        "id": "xxx",
        "name": "xxx",
        "msg_direct"："这是自动发送的消息 【也可以直接使用这个配置发送】"
    }
]


# ============================================

def check_window_open(driver):
    """检测聊天窗口是否已打开"""
    try:
        WebDriverWait(driver, 2).until(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'public-DraftEditor-content')]"))
        )
        return True
    except:
        return False


def safe_close_window(driver):
    """安全关闭当前窗口，如果卡死则跳过"""
    try:
        driver.close()
    except Exception as e:
        pass


def send_douyin_msg():
    # --- Chrome 浏览器初始化 ---
    options = Options()
    options.add_argument(f"--user-data-dir={USER_DATA_PATH}")
    options.add_argument("--profile-directory=Default")

    # --- 日志屏蔽终极方案 (Chrome版) ---
    options.add_argument("--log-level=3")  # 只显示致命错误
    options.add_argument("--silent")
    options.add_argument("--disable-logging")
    # 屏蔽 USB 报错和自动化提示条
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

    # Service args: 压制驱动日志
    service = Service(executable_path=DRIVER_PATH, args=['--log-level=OFF'])

    # 启动 Chrome
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    try:
        wait = WebDriverWait(driver, 15)
        actions = ActionChains(driver)

        print("🚀 启动 Chrome 脚本，进入抖音...")
        driver.get("https://www.douyin.com/")

        # --- 开始循环发送 ---
        for index, user in enumerate(TARGET_USERS):
            try:
                print(f"\n[{index + 1}/{len(TARGET_USERS)}] 正在处理用户: {user['name']}")

                # 1. 准备消息
                if "date" in user and "template" in user:
                    d_cnt = calculate_days_from_today(user["date"])
                    final_message = user["template"].format(days=d_cnt)
                else:
                    final_message = user.get("msg_direct", "你好")

                # 2. 定位搜索框
                print("🔍 定位搜索框...")
                try:
                    search_input = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-e2e='searchbar-input']")
                    ))
                except:
                    driver.refresh()
                    search_input = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-e2e='searchbar-input']")
                    ))

                # 智能登录检测
                try:
                    search_input.click()
                except ElementClickInterceptedException:
                    print("\n🛑 检测到登录弹窗！请扫码登录，完成后按回车...")
                    input()
                    print("✅ 继续执行，刷新页面...")
                    driver.refresh()
                    time.sleep(3)
                    search_input = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='searchbar-input']")))
                    search_input.click()

                # 输入搜索内容
                search_input.send_keys(Keys.CONTROL + "a")
                search_input.send_keys(Keys.BACKSPACE)
                search_input.send_keys(user['id'])
                time.sleep(0.5)
                search_input.send_keys(Keys.ENTER)

                # 3. 点击用户链接
                print(f"🔍 搜索结果定位: {user['name']}")
                windows_before = driver.window_handles

                user_link_xpath = f"//div[@id='search-content-area']//a[contains(@href, '/user/') and contains(., '{user['name']}')]"
                user_link = wait.until(EC.element_to_be_clickable((By.XPATH, user_link_xpath)))
                user_link.click()

                # 4. 切换新窗口 (先切后关，且允许关闭失败)
                print("⏳ 等待新标签页...")
                wait.until(EC.new_window_is_opened(windows_before))

                windows_after = driver.window_handles
                new_page_handle = [h for h in windows_after if h not in windows_before][0]

                # 尝试清理旧窗口 (内存优化)
                if len(windows_after) > 1:
                    safe_close_window(driver)

                # 强制切到新窗口
                driver.switch_to.window(new_page_handle)
                time.sleep(2)

                # 5. 寻找私信按钮
                print("🖱️ 寻找私信按钮...")
                target_xpath = '//*[@id="user_detail_element"]/div/div[2]/div[3]/div[3]/div[1]/button[2]'
                chat_btn = None
                try:
                    chat_btn = wait.until(EC.presence_of_element_located((By.XPATH, target_xpath)))
                except:
                    # 模糊匹配
                    btns = driver.find_elements(By.XPATH, "//button[contains(., '私信')]")
                    for b in btns:
                        if b.is_displayed() and b.location['y'] > 100:
                            chat_btn = b
                            break

                if not chat_btn:
                    raise Exception("未找到私信按钮")

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chat_btn)
                time.sleep(1)

                # 点击逻辑 (防 React 拦截)
                if not check_window_open(driver):
                    try:
                        actions.move_to_element(chat_btn).pause(0.5).click().perform()
                    except:
                        pass

                if not check_window_open(driver):
                    driver.execute_script("arguments[0].click();", chat_btn)

                # 6. 发送消息
                print("✍️ 等待输入框...")
                input_xpath = "//div[contains(@class, 'public-DraftEditor-content') and @contenteditable='true']"
                input_box = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, input_xpath))
                )

                driver.execute_script("arguments[0].focus();", input_box)
                actions.move_to_element(input_box).click().perform()

                print(f"⌨️ 发送给 [{user['name']}]: {final_message}")
                actions.send_keys(final_message).perform()
                actions.send_keys(" ").send_keys(Keys.BACKSPACE).perform()  # 激活发送按钮
                time.sleep(1)

                try:
                    send_btn = driver.find_element(By.CSS_SELECTOR, ".e2e-send-msg-btn")
                    actions.move_to_element(send_btn).click().perform()
                except:
                    actions.send_keys(Keys.ENTER).perform()

                print(f"✅ [{user['name']}] 发送成功！")
                time.sleep(2)

            except Exception as e:
                print(f"❌ 处理用户 [{user['name']}] 时出错: {e}")
                # 容错切换，防止卡死
                try:
                    if len(driver.window_handles) > 0:
                        driver.switch_to.window(driver.window_handles[-1])
                except:
                    pass
                continue

        print("\n🎉 所有用户处理完毕！")

    except Exception as e:
        print(f"❌ 全局错误: {e}")
    finally:
        print("🛑 关闭浏览器...")
        driver.quit()


if __name__ == "__main__":

    send_douyin_msg()
