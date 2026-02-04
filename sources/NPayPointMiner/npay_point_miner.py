import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 사용자 설정 ---
NAVER_ID = 'your_id'
NAVER_PW = 'your_pw'
MISSION_URL = "https://point.pay.naver.com/pc/mission-detail?dataType=placement&rank=1&pageKey=benefit_group_pp&rankType=RANDOM_DAILY&sortCompletedAdToLast=true&mssCode=pp"

def create_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # 창이 뜨지 않길 원하면 아래 주석 해제 (단, 첫 실행은 디버깅을 위해 켜두는 걸 권장)
    # options.add_argument("--headless") 
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def login_naver(driver, id, pw):
    print("🔐 네이버 로그인 중...")
    driver.get("https://nid.naver.com/nidlogin.login")
    time.sleep(2)
    try:
        # 캡차 우회를 위한 자바스크립트 입력 방식
        driver.execute_script(f"document.getElementById('id').value = '{id}';")
        driver.execute_script(f"document.getElementById('pw').value = '{pw}';")
        time.sleep(1)
        driver.find_element(By.ID, "log.login").click()
        
        # 로그인 성공 여부 대기 (GNB 영역 확인)
        WebDriverWait(driver, 15).until(EC.url_contains("naver.com"))
        print("✅ 로그인 완료")
        return True
    except Exception as e:
        print(f"❌ 로그인 실패: {e}")
        return False

def run_mission_bot():
    driver = create_driver()
    
    try:
        if not login_naver(driver, NAVER_ID, NAVER_PW):
            return

        print(f"🚀 미션 페이지 접속: {MISSION_URL}")
        driver.get(MISSION_URL)
        time.sleep(3)

        # 1. 클릭 대상 요소(광고 아이템) 모두 찾기
        # 클래스명에 'PlacementList_item__'이 포함된 모든 li 태그를 타겟팅합니다.
        items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[class*='PlacementList_item__']"))
        )
        
        total = len(items)
        print(f"🔎 총 {total}개의 클릭 미션을 발견했습니다.")

        for i in range(total):
            try:
                # 페이지 갱신 대응을 위해 매번 요소를 새로 고침
                current_items = driver.find_elements(By.CSS_SELECTOR, "li[class*='PlacementList_item__']")
                target = current_items[i]

                # 해당 요소로 스크롤 (중앙 정렬)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                time.sleep(1)

                print(f"👉 [{i+1}/{total}] 미션 클릭 중...")
                target.click()
                
                # 2. 새 탭 제어 (포인트 적립의 핵심)
                time.sleep(2) # 탭이 뜨는 시간
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[1]) # 새 탭으로 이동
                    
                    # 페이지 로딩 및 포인트 적립 유효 시간 대기 (중요)
                    time.sleep(4) 
                    
                    driver.close() # 새 탭 닫기
                    driver.switch_to.window(driver.window_handles[0]) # 메인 탭 복귀
                    print(f"✅ [{i+1}/{total}] 적립 완료 및 복귀")
                
                time.sleep(1) # 과부하 방지를 위한 짧은 휴식

            except Exception as e:
                print(f"⚠️ [{i+1}번] 처리 중 오류 발생 (이미 완료되었을 수 있음): {e}")
                # 오류 발생 시에도 메인 탭으로 안전하게 복귀
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                continue

        print("\n✨ 오늘의 모든 미션을 확인했습니다!")

    except Exception as e:
        print(f"🚨 치명적 오류 발생: {e}")
    finally:
        print("🏁 프로그램을 종료합니다.")
        driver.quit()

if __name__ == "__main__":
    run_mission_bot()