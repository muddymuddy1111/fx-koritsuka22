# fx-koritsuka22

個人利用向けの **FX監視ダッシュボード（Streamlit）** です。  
1日3回（朝・昼・夜）に確認するだけで、以下を素早く判断できる構成です。

- 市場環境（リスクオン／オフ）
- 通貨強弱（USD/JPY/CHF/CAD）
- 押し目・戻り目の有無
- エントリー優位性（★評価）

## 対象

- USD/JPY
- CHF/JPY
- CAD/JPY
- USD/CHF
- USD/CAD
- 補助: WTI・S&P500

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 実行

```bash
streamlit run app.py
```

## OANDA API利用（任意）

環境変数を設定すると、OANDAデモAPIからローソク足を取得します。  
未設定時は、アプリが自動で疑似データを生成して画面確認可能です。

```bash
export OANDA_API_TOKEN="your_token"
export OANDA_BASE_URL="https://api-fxpractice.oanda.com/v3"
```

## ファイル構成

- `app.py` : Streamlit UI
- `data.py` : OANDA API取得
- `indicators.py` : テクニカル指標計算
- `strength.py` : 通貨強弱スコア
- `environment.py` : 市場環境判定
- `ai_model.py` : RandomForest によるAI確率推定
- `alerts.py` : エントリー優位性スコア
- `config.py` : 設定値
