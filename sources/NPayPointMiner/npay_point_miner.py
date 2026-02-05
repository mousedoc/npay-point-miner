import time
import platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from sources.TelegramUtil.telegram_util import TelegramUtil


class NPayPointMiner:

    # --- 사용자 설정 ---
    _naver_id = 'your_id'
    _naver_pw = 'your_pw'

    # 미션 설정 데이터: (URL, 해당 페이지의 아이템 클래스 식별자)
    _missions = [
        ("https://point.pay.naver.com/pc/mission-detail?dataType=placement&rank=1&pageKey=benefit_group_pp&rankType=RANDOM_DAILY&sortCompletedAdToLast=true&mssCode=pp", "PlacementList_item__"),
        ("https://point.pay.naver.com/pc/mission-detail?dataType=category&rank=3&pageKey=shopping&rankType=DESC&sortCompletedAdToLast=false&mssCode=nvshopping", "BenefitList_item__"),
        ("https://point.pay.naver.com/pc/mission-detail?dataType=category&rank=8&pageKey=insurance&rankType=DESC&sortCompletedAdToLast=false&mssCode=insurance", "BenefitList_item__")
    ]

    # 텔레그램 설정
    _use_telegram_log = False

    @classmethod
    def is_linux_platform(cls):
        return platform.system() == "Linux"
    
    def _initialize(self):
        self._init_naver_account_info()
        self._init_telegram_log_option()

    def _init_naver_account_info(self):
        self._naver_id = ''
        self._naver_pw = ''

    def _init_telegram_log_option(self):
        self._use_telegram_log = NPayPointMiner.is_linux_platform()

    def _create_driver(self):
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        if NPayPointMiner.is_linux_platform():
            options.add_argument("--headless")  # 창 없는 모드
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")

        self._driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def _release_driver(self);
        if self._driver is None:
            return

        # 드라이버가 있을 때만 실행할 로직
        self._driver.quit()

    def _login(self):
        self.print_log("🔐 네이버 로그인 중...")
        self._driver.get("https://nid.naver.com/nidlogin.login")

        try:
            # 1. 아이디 입력창이 뜰 때까지 최대 10초 대기
            wait = WebDriverWait(driver, 10)
            id_input = wait.until(EC.presence_of_element_located((By.ID, "id")))
            
            # 2. 자바스크립트로 값 입력 (캡차 방지)
            self._driver.execute_script(f"document.getElementById('id').value = '{id}';")
            self._driver.execute_script(f"document.getElementById('pw').value = '{pw}';")
            
            # 3. 로그인 버튼이 클릭 가능한 상태인지 확인 후 클릭
            login_btn = wait.until(EC.element_to_be_clickable((By.ID, "log.login")))
            login_btn.click()
            
            # 4. 로그인 성공 여부 체크
            # URL이 변경되거나, 특정 로그아웃 버튼/내 프로필 정보가 나타나는지 확인
            # 아래는 '로그아웃' 버튼이 나타나면 로그인이 성공한 것으로 판단하는 예시입니다.
            wait.until(lambda d: "nid.naver.com" not in d.current_url or d.find_elements(By.CLASS_NAME, "gnb_btn_login"))
            
            self.print_log("✅ 로그인 완료")
            return True
        except Exception as e:
            self.print_log(f"❌ 로그인 중 오류 발생: {e}")
            return False
        
    def _process_mining(self):
        """설정된 모든 미션 페이지를 순회하며 적립을 수행합니다."""
        for url, class_suffix in self._missions:
            try:
                self._run_single_mission_page(url, class_suffix)
            except Exception as e:
                self.print_log(f"🚨 페이지 처리 중 치명적 오류 ({url}): {e}")
        
        self.print_log("\n✨ 모든 카테고리의 미션을 확인했습니다!")

    def _run_single_mission_page(self, url, class_suffix):
        """단일 페이지 내의 모든 광고를 클릭합니다."""
        self.print_log(f"🚀 미션 페이지 접속: {url}")
        self._driver.get(url)
        
        # 페이지 로딩 대기 (아이템이 하나라도 나타날 때까지)
        try:
            css_selector = f"li[class*='{class_suffix}']"
            WebDriverWait(self._driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        except:
            self.print_log(f"ℹ️ 해당 페이지에 진행 가능한 미션이 없습니다.")
            return

        # 아이템 개수 파악
        items = self._driver.find_elements(By.CSS_SELECTOR, css_selector)
        total = len(items)
        self.print_log(f"🔎 총 {total}개의 클릭 미션을 발견했습니다.")

        for i in range(total):
            try:
                # 갱신 대응을 위해 매번 요소 다시 찾기
                current_items = self._driver.find_elements(By.CSS_SELECTOR, css_selector)
                target = current_items[i]

                # 스크롤 및 클릭
                self._driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                time.sleep(1)
                
                target.click()
                self.print_log(f"👉 [{i+1}/{total}] 클릭 중...")

                # 새 탭 제어 로직 호출
                self._handle_new_tab()

            except Exception as e:
                self.print_log(f"⚠️ [{i+1}번] 처리 중 오류: {e}")
                self._ensure_main_window() # 오류 시 메인창 복귀 보장
                continue

    def _handle_new_tab(self):
        """새로 열린 탭으로 이동하여 대기 후 닫습니다."""
        time.sleep(2) # 탭 생성 대기
        if len(self._driver.window_handles) > 1:
            self._driver.switch_to.window(self._driver.window_handles[1])
            time.sleep(4) # 적립 대기 시간
            self._driver.close()
            self._driver.switch_to.window(self._driver.window_handles[0])
            self.print_log("✅ 적립 완료 후 복귀")

    def _ensure_main_window(self):
        """탭이 꼬였을 경우 메인 창으로 강제 복귀합니다."""
        if len(self._driver.window_handles) > 1:
            for handle in self._driver.window_handles[1:]:
                self._driver.switch_to.window(handle)
                self._driver.close()
        self._driver.switch_to.window(self._driver.window_handles[0])


    def run(self):
        self._initialize()
        
        try:
            if not self.login_naver():
                self.print_log(f"🚨 로그인 실패")
                return

            self._process_mining()
        except Exception as e:
            self.print_log(f"🚨 치명적 오류 발생: {e}")
        finally:
            self._release_driver()
            self.print_log("🏁 프로그램을 종료합니다.")

    def _print_log_log(self, msg):
        # CLI 
        self.print_log(msg)

        # Telegram
        if self.send_telegram is True:
            TelegramUtil.send_message(msg)

if __name__ == "__main__":
    miner = NPayPointMiner()
    miner.run()