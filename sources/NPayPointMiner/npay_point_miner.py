import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from sources.TelegramUtil.telegram_util import TelegramUtil
from sources.CommonUtil.common_util import CommonUtil

class NPayPointMiner:
    # --- 클래스 속성 ---
    _naver_id = ''
    _naver_pw = ''
    _driver = None
    
    # 인스턴스 생성 시점에 환경 판별하여 미리 설정 - Github Actions 환경에서만 텔레그램 로그 전송 사용
    _use_telegram_log = os.environ.get('GITHUB_ACTIONS') == 'true'

    _missions = [
        ("https://point.pay.naver.com/pc/mission-detail?dataType=placement&rank=1&pageKey=benefit_group_pp&rankType=RANDOM_DAILY&sortCompletedAdToLast=true&mssCode=pp", "PlacementList_item__"),
        ("https://point.pay.naver.com/pc/mission-detail?dataType=category&rank=3&pageKey=shopping&rankType=DESC&sortCompletedAdToLast=false&mssCode=nvshopping", "BenefitList_item__"),
        ("https://point.pay.naver.com/pc/mission-detail?dataType=category&rank=8&pageKey=insurance&rankType=DESC&sortCompletedAdToLast=false&mssCode=insurance", "BenefitList_item__")
    ]

    @staticmethod
    def is_github_actions():
        return os.environ.get('GITHUB_ACTIONS') == 'true'

    def _initialize(self):
        self._init_account_info()
        # 텔레그램 옵션 초기화는 속성 선언 시점으로 이동했으므로 생략 가능하거나 확인 용도로 사용

    def _init_account_info(self):
        if self.is_github_actions():
            self._init_naver_account_info_server()
        else:
            self._init_naver_account_info_local()

    def _init_naver_account_info_server(self):
        self.print_log("🌐 GitHub Actions 환경: Secrets 변수로부터 정보를 로드합니다.")
        self._naver_id = os.environ.get('NAVER_ID', '')
        self._naver_pw = os.environ.get('NAVER_PW', '')
                
        # 마스킹된 로그 출력
        masked_id = CommonUtil.mask_string(self._naver_id)
        masked_pw = CommonUtil.mask_string(self._naver_pw)
        self.print_log(f"✅ 로드된 계정: ID({masked_id}), PW({masked_pw})")

    def _init_naver_account_info_local(self):
            filename = 'config.txt'
            self.print_log(f"🌐 로컬 환경: {filename}에서 정보를 로드합니다.")
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#') or '=' not in line: continue
                        key, value = line.split('=', 1)
                        if key.strip().upper() == 'ID': self._naver_id = value.strip()
                        elif key.strip().upper() == 'PW': self._naver_pw = value.strip()
                
                # 💡 수정: 유효성 검사 후 마스킹 로그 출력
                if not self._naver_id or not self._naver_pw:
                    self.print_log("⚠️ 계정 정보가 비어있습니다. config.txt를 확인하세요.")
                else:
                    masked_id = CommonUtil.mask_string(self._naver_id)
                    masked_pw = CommonUtil.mask_string(self._naver_pw)
                    self.print_log(f"✅ 계정 정보 로드 성공: ID({masked_id}), PW({masked_pw})")
            except FileNotFoundError:
                self.print_log(f"❌ {filename} 파일을 찾을 수 없습니다.")
            
    def _create_driver(self):
        options = Options()
        # 자동화 감지 우회 옵션들
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

        if self.is_github_actions():
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")

        self._driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # [우회 핵심] navigator.webdriver 속성 제거
        self._driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })

    def _login(self):
        if not self._driver: return False
        self.print_log("🔐 네이버 로그인 시도 중...")
        self._driver.get("https://nid.naver.com/nidlogin.login")
        try:
            wait = WebDriverWait(self._driver, 10)
            wait.until(EC.presence_of_element_located((By.ID, "id")))
            self._driver.execute_script(f"document.getElementById('id').value = '{self._naver_id}';")
            self._driver.execute_script(f"document.getElementById('pw').value = '{self._naver_pw}';")
            wait.until(EC.element_to_be_clickable((By.ID, "log.login"))).click()
            
            # 로그인 성공 판별 (메인 페이지 이동 시까지 최대 15초 대기)
            wait.until(lambda d: "nid.naver.com" not in d.current_url or d.find_elements(By.CLASS_NAME, "gnb_my_name"))
            self.print_log("✅ 네이버 로그인 완료")
            return True
        except Exception as e:
            self.print_log(f"❌ 로그인 중 오류 발생: {e}")
            return False

    def _run_single_mission_page(self, url, class_suffix):
        self.print_log(f"🚀 미션 페이지 접속: {url}")
        self._driver.get(url)
        css_selector = f"li[class*='{class_suffix}']"
        try:
            WebDriverWait(self._driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        except:
            self.print_log("ℹ️ 진행 가능한 미션 아이템이 없습니다.")
            return

        items = self._driver.find_elements(By.CSS_SELECTOR, css_selector)
        total = len(items)
        self.print_log(f"🔎 총 {total}개의 미션을 발견했습니다.")

        for i in range(total):
            try:
                # 갱신 대응: 요소를 매번 새로 찾음
                target = self._driver.find_elements(By.CSS_SELECTOR, css_selector)[i]
                self._driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                time.sleep(1)
                target.click()
                self.print_log(f"👉 [{i+1}/{total}] 클릭 완료")
                self._handle_new_tab()
            except Exception as e:
                self.print_log(f"⚠️ [{i+1}번] 처리 실패: {e}")
                self._ensure_main_window()
                continue

    def _handle_new_tab(self):
        time.sleep(2)
        if len(self._driver.window_handles) > 1:
            self._driver.switch_to.window(self._driver.window_handles[1])
            time.sleep(5) 
            self._driver.close()
            self._driver.switch_to.window(self._driver.window_handles[0])

    def _ensure_main_window(self):
        while len(self._driver.window_handles) > 1:
            self._driver.switch_to.window(self._driver.window_handles[-1])
            self._driver.close()
        self._driver.switch_to.window(self._driver.window_handles[0])

    def print_log(self, msg):
        print(msg)
        if self._use_telegram_log:
            try: TelegramUtil.send_message(msg)
            except: pass

    def run(self):
        self._initialize()
        
        # 💡 추가: 로그인 시도 전 계정 정보 존재 여부 최종 확인
        if not self._naver_id or not self._naver_pw:
            self.print_log("🚨 [중단] 계정 정보가 누락되어 프로그램을 종료합니다.")
            return

        self._create_driver()
        try:
            if not self._login():
                self.print_log("🚨 로그인 실패로 중단")
                return
            
            self.print_log("💰 포인트 채굴 시작")
            for url, class_suffix in self._missions:
                self._run_single_mission_page(url, class_suffix)
        except Exception as e:
            self.print_log(f"🚨 치명적 오류: {e}")
        finally:
            if self._driver:
                self._driver.quit()
            self.print_log("🏁 종료")
            
if __name__ == "__main__":
    miner = NPayPointMiner()
    miner.run()