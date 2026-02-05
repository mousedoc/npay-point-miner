import time
import os
import random
import pickle
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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

    # 쿠키 경로
    _cookie_path = 'cookie.txt'

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
        self._print_log("🌐 GitHub Actions 환경: Secrets 변수로부터 정보를 로드합니다.")
        self._naver_id = os.environ.get('NAVER_ID', '')
        self._naver_pw = os.environ.get('NAVER_PW', '')
                
        # 마스킹된 로그 출력
        masked_id = CommonUtil.mask_string(self._naver_id)
        masked_pw = CommonUtil.mask_string(self._naver_pw)
        self._print_log(f"✅ 로드된 계정: ID({masked_id}), PW({masked_pw})")

    def _init_naver_account_info_local(self):
            filename = 'config.txt'
            self._print_log(f"🌐 로컬 환경: {filename}에서 정보를 로드합니다.")
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
                    self._print_log("⚠️ 계정 정보가 비어있습니다. config.txt를 확인하세요.")
                else:
                    masked_id = CommonUtil.mask_string(self._naver_id)
                    masked_pw = CommonUtil.mask_string(self._naver_pw)
                    self._print_log(f"✅ 계정 정보 로드 성공: ID({masked_id}), PW({masked_pw})")
            except FileNotFoundError:
                self._print_log(f"❌ {filename} 파일을 찾을 수 없습니다.")
            
    def _create_driver(self):
        options = Options()
        
        # 자동화 감지 우회 옵션들
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        options.page_load_strategy = 'eager'
        
        # if self.is_github_actions():    
        options.add_argument("--window-size=1920,1080") # 실제 브라우저처럼 크기 지정
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
        
        if self.is_github_actions():
            self.load_cookies()
        
        if not self._driver: return False
        self._print_log("🔐 네이버 로그인 시도 중...")
        self._driver.get("https://nid.naver.com/nidlogin.login")
        try:
            wait = WebDriverWait(self._driver, 10)
            wait.until(EC.presence_of_element_located((By.ID, "id")))
            self._driver.execute_script(f"document.getElementById('id').value = '{self._naver_id}';")
            self._driver.execute_script(f"document.getElementById('pw').value = '{self._naver_pw}';")
            wait.until(EC.element_to_be_clickable((By.ID, "log.login"))).click()
            
            # 로그인 성공 판별 (메인 페이지 이동 시까지 최대 15초 대기)
            wait.until(lambda d: "nid.naver.com" not in d.current_url or d.find_elements(By.CLASS_NAME, "gnb_my_name"))
            self._print_log("✅ 네이버 로그인 완료")
            
            if self.is_github_actions() == False:
                self.save_cookies()
            
            return True
        except Exception as e:
            self._print_log(f"❌ 로그인 중 오류 발생: {e}")
            self._driver.save_screenshot("debug_exception.png")
            return False

    def _get_npay_balance(self, print_balance = True):
        """추출된 금액 문자열에서 숫자만 골라 정수(int)로 반환합니다."""
        try:
            self._print_log("💰 잔액 확인 중...")
            self._driver.get("https://home.pay.naver.com/pc")
            
            wait = WebDriverWait(self._driver, 10)
            
            # '잔액' blind 요소를 포함한 부모 요소를 찾음
            balance_xpath = "//span[@class='blind' and contains(., '잔액')]/parent::*"
            wait.until(EC.presence_of_element_located((By.XPATH, balance_xpath)))
            
            parent_el = self._driver.find_element(By.XPATH, balance_xpath)
            raw_text = parent_el.text.strip() # 예: "잔액 123,456원"
            
            # 💡 정규표현식을 사용하여 숫자만 모두 찾아 합침
            # \d는 숫자를 의미하며, findall은 숫자 부분만 리스트로 반환함
            numbers_only = "".join(re.findall(r'\d+', raw_text))
            
            if numbers_only:
                balance_int = int(numbers_only)
                
                if print_balance:
                    self._print_log(f"✅ 현재 네이버 페이 잔액: {balance_int:,}원 (정수 변환 완료)")
                
                return balance_int
            
            self._print_log("⚠️ 잔액 숫자를 찾을 수 없습니다.")
            return 0

        except Exception as e:
            self._print_log(f"❌ 잔액 확인 실패: {e}")
            return 0
                
    def save_cookies(self):
        """현재 브라우저의 쿠키를 파일로 저장합니다."""
        try:
            cookies = self._driver.get_cookies()
            with open(self._cookie_path, "wb") as f:
                pickle.dump(cookies, f)
            self._print_log(f"✅ 쿠키 저장 완료: {self._cookie_path} ({len(cookies)}개)")
        except Exception as e:
            self._print_log(f"❌ 쿠키 저장 실패: {e}")

    def load_cookies(self):
        """파일에서 쿠키를 읽어와 현재 브라우저 세션에 주입합니다."""
        try:
            with open(self._cookie_path, "rb") as f:
                cookies = pickle.load(f)
            
            # 쿠키를 추가하기 전, 해당 도메인(naver.com)에 먼저 접속해야 합니다.
            self._driver.get("https://www.naver.com")
            time.sleep(1)

            for cookie in cookies:
                # 쿠키 데이터 중 'expiry'가 float인 경우 간혹 에러가 날 수 있어 정수형 변환 처리
                if 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])
                self._driver.add_cookie(cookie)
                
            self._print_log(f"✅ 쿠키 로드 및 주입 완료 ({len(cookies)}개)")
            
            # 주입 후 페이지 새로고침을 해야 로그인 상태가 반영됩니다.
            self._driver.refresh()
            return True
        except FileNotFoundError:
            self._print_log(f"⚠️ {self._cookie_path} 파일을 찾을 수 없습니다.")
            return False
        except Exception as e:
            self._print_log(f"❌ 쿠키 로드 실패: {e}")
            return False


    def _run_single_mission_page(self, url, class_suffix):
        self._print_log(f"🚀 미션 페이지 접속: {url}")
        self._driver.get(url)
        css_selector = f"li[class*='{class_suffix}']"
        
        try:
            WebDriverWait(self._driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        except:
            self._print_log("ℹ️ 진행 가능한 미션 아이템이 없습니다.")
            return

        items = self._driver.find_elements(By.CSS_SELECTOR, css_selector)
        total = len(items)
        self._print_log(f"🔎 총 {total}개의 미션을 발견했습니다.")

        for i in range(total):
            try:
                time.sleep(1)
                
                self._handle_subscription_modal()

                # 갱신 대응: 요소를 매번 새로 찾음
                target = self._driver.find_elements(By.CSS_SELECTOR, css_selector)[i]
                self._driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                time.sleep(1)
                
                target.click()
                self._print_log(f"👉 [{i+1}/{total}] 클릭 완료")
                self._handle_new_tab()

            except Exception as e:
                self._print_log(f"⚠️ [{i+1}번] 처리 실패: {e}")
                self._ensure_main_window()
                continue
            
    def _handle_subscription_modal(self):
        """구독 유도 모달을 탐색하고 발견 시 '다시 보지 않기' 또는 '닫기'를 클릭합니다."""
        try:
            # 모달 존재 여부 확인 (최대한 가벼운 선택자 사용)
            modals = self._driver.find_elements(By.CSS_SELECTOR, "[class*='SubscriptionAdModal_article__']")
            if not modals:
                return

            self._print_log("🔔 구독 유도 모달 발견: 제거 프로세스 시작")
            
            # 1순위: '다시 보지 않기' 버튼 (가장 확실한 차단)
            # 2순위: 우측 상단 'X' 버튼 (ModalFrame-module_button-close__)
            close_selectors = [
                "button[class*='SubscriptionAdModal_button-hide__']", 
                "button[class*='ModalFrame-module_button-close__']"
            ]

            for selector in close_selectors:
                btns = self._driver.find_elements(By.CSS_SELECTOR, selector)
                if btns and btns[0].is_displayed():
                    self._driver.execute_script("arguments[0].click();", btns[0])
                    self._print_log(f"✅ 모달 제거 완료 ({selector.split('-')[-1]})")
                    time.sleep(1)
                    return
        except Exception as e:
            self._print_log(f"⚠️ 모달 처리 중 비정상 에러: {e}")
            
    def _handle_new_tab(self):
        """새 탭 제어 및 팝업 처리 로직"""
        # 탭이 생성될 때까지 최소 대기
        time.sleep(1.5) 
        
        if len(self._driver.window_handles) <= 1:
            return

        # 새 탭으로 전환
        self._driver.switch_to.window(self._driver.window_handles[1])
        
        # 1. 레이어 팝업 처리 (JS 클릭 적용)
        self._click_popup_layer_if_exists()

        # 2. 클릭 후 아주 짧은 숨 고르기
        time.sleep(random.uniform(5.5, 7.5))
        
        self._driver.close()
        self._driver.switch_to.window(self._driver.window_handles[0])

    def _click_popup_layer_if_exists(self):
        popup_types = ["type_has_points", "type_no_points", "type_out_of_period"]
        
        # 1. 스크립트 실행 타임아웃을 1초로 제한 (기본값은 무제한에 가까움)
        self._driver.set_script_timeout(1)
        
        for p_type in popup_types:
            try:
                popups = self._driver.find_elements(By.CSS_SELECTOR, f"div[class*='layer_popup'][class*='{p_type}']")
                if popups and popups[0].is_displayed():
                    btn = popups[0].find_element(By.CSS_SELECTOR, ".popup_link")
                    
                    self._print_log(f"🚀 비동기 클릭 강제 실행 ({p_type})")
                    
                    try:
                        # 2. 아주 짧은 타임아웃 내에 실행 시도
                        self._driver.execute_script(
                            "var el = arguments[0]; setTimeout(function() { el.click(); }, 0);", 
                            btn
                        )
                    except TimeoutException:
                        # 3. 타임아웃이 나더라도 클릭 명령은 브라우저에 전달되었을 확률이 높으므로 무시
                        self._print_log("⏳ 타임아웃 발생 (무시하고 진행)")
                        pass
                    
                    return True 
            except Exception as e:
                continue
        return False    
            
    def _ensure_main_window(self):
        while len(self._driver.window_handles) > 1:
            self._driver.switch_to.window(self._driver.window_handles[-1])
            self._driver.close()
        self._driver.switch_to.window(self._driver.window_handles[0])

    def _print_log(self, msg):
        print(msg)
        if self._use_telegram_log:
            try: TelegramUtil.send_message(msg)
            except: pass

    def _report_mining_result(self, before_balance, after_balance):
        """채굴 전후 잔액을 비교하여 결과를 출력하고 전송합니다."""
        
        # 차액 계산
        profit = after_balance - before_balance
        
        # 💡 {값:,} 형식을 사용하면 세 자리마다 콤마가 자동으로 찍힙니다.
        before_str = f"{before_balance:,}"
        after_str = f"{after_balance:,}"
        profit_str = f"{profit:,}"
        
        self._print_log(f"--- 📊 채굴 결과 보고 ---")
        self._print_log(f"💰 시작 잔액: {before_str}원")
        self._print_log(f"💰 종료 잔액: {after_str}원")
        
        if profit > 0:
            msg = f"✅ 오늘의 수익: +{profit_str}원!"
        elif profit < 0:
            msg = f"🔻 잔액 감소: {profit_str}원 (확인 필요)"
        else:
            msg = "ℹ️ 변동 사항 없음"
            
        self._print_log(msg)
        
        # 텔레그램 전송 (콤마가 포함된 문자열 사용)
        report_text = (
            f"⛏️ **NPay Miner Report**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 시작: {before_str}원\n"
            f"💵 종료: {after_str}원\n"
            f"✨ **수익: +{profit_str}원**"
        )
        TelegramUtil.send_message(report_text)

    def run(self):
        self._initialize()
        
        # 💡 추가: 로그인 시도 전 계정 정보 존재 여부 최종 확인
        if not self._naver_id or not self._naver_pw:
            self._print_log("🚨 [중단] 계정 정보가 누락되어 프로그램을 종료합니다.")
            return

        before_balance = 0
        after_balance = 0

        self._create_driver()
        try:
            if not self._login():
                self._print_log("🚨 로그인 실패로 중단")
                return
            
            before_balance = self._get_npay_balance()
            
            self._print_log("💰 포인트 채굴 시작")
            for url, class_suffix in self._missions:
                self._run_single_mission_page(url, class_suffix)
                
        except Exception as e:
            self._print_log(f"🚨 치명적 오류: {e}")
        finally:
            after_balance = self._get_npay_balance()

            if self._driver:
                self._driver.quit()
                
            self._report_mining_result(before_balance, after_balance)
            self._print_log("🏁 종료")
            
if __name__ == "__main__":
    miner = NPayPointMiner()
    miner.run()