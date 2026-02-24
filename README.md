# npay-point-miner
Naver Pay Free Point Miner
Automated daily point collection using Selenium and GitHub Actions.

---

# 🚀 Quickstart - Local

Follow these steps to run the miner directly on your local machine.

```bash
# 1. Clone the repository
git clone [https://github.com/your-username/npay-point-miner.git](https://github.com/your-username/npay-point-miner.git)
cd npay-point-miner

# 2. Configure account credentials
# Open config.txt and enter your Naver ID and Password.
echo "ID=your_id" > config.txt
echo "PW=your_password" >> config.txt

# 3. Install required dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

# ⚙️ Quickstart - GitHub Actions (currently, not work)
<samp>⚠️ **Automated Naver login via GitHub Actions is currently blocked by CAPTCHA authentication**</samp>

Automate your point mining by setting up GitHub Actions to run daily without keeping your computer on.

### 1. Configure Repository Secrets
Navigate to **Settings > Secrets and variables > Actions** in your GitHub repository and add the following secrets:
* `NAVER_ID`: Your Naver account ID
* `NAVER_PW`: Your Naver account password
* `TELEGRAM_TOKEN`: (Optional) Your Telegram Bot Token
* `TELEGRAM_CHAT_ID`: (Optional) Your Telegram Chat ID

### 2. Workflow Configuration (`.github/workflows/run.yml`)
Run github actions at `.github/workflows/daily-run.yml`

