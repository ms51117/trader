class MarketConditionClassifier:
    def __init__(self):
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )

    def prepare_features(self, df):
        # ویژگی‌های تکنیکال برای پیش‌بینی روند سالم
        features = pd.DataFrame()
        features['returns'] = df['close'].pct_change()
        features['volatility'] = df['returns'].rolling(20).std()
        features['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        features['rsi'] = calculate_rsi(df['close'])
        features['macd'] = calculate_macd(df['close'])
        features['adx'] = calculate_adx(df)
        features['atr'] = df['atr']

        # برچسب: آیا 5 کندل بعدی روند صعودی داشت؟ (1 = بله، 0 = خیر)
        features['target'] = (df['close'].shift(-5) > df['close']).astype(int)

        return features.dropna()

    def train(self, features):
        X = features.drop('target', axis=1)
        y = features['target']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)

        # ارزیابی
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model Accuracy: {accuracy:.2%}")

    def predict(self, current_features):
        proba = self.model.predict_proba(current_features.reshape(1, -1))
        return proba[0][1]  # احتمال روند سالم
