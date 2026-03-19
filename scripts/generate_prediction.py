#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_prediction.py - 生成预测逻辑
Generate Prediction Logic

功能:
- 生成预测脚本（支持多模型自动对比）
- 自动选择最优模型
- 配置 OpenClaw Cron 任务
- 保存预测配置

Usage:
    python generate_prediction.py --target "未来 30 天数据趋势预测" --models auto --env-file .env
"""

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv


def generate_script(target, model_type, parameters, config):
    """生成预测脚本 - 支持多模型对比"""
    table_name = parameters.get("table", "your_table")
    date_column = parameters.get("date_column", "created_at")
    metric_column = parameters.get("metric_column", "metric_value")
    timestamp = datetime.now()
    prediction_id = f"pred_{timestamp.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    date_dir = Path(config["records_dir"]) / "predictions" / timestamp.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    
    results_dir = date_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = results_dir / f"{prediction_id}_result.json"
    script_file = date_dir / f"{prediction_id}.py"
    
    # 支持的模型列表
    if model_type == "auto":
        models_to_run = ["arima", "linear_regression", "lasso", "exponential_smoothing", "prophet"]
    else:
        models_to_run = [model_type]
    
    # 生成脚本内容（多模型对比版本）
    script_content = f'''#!/usr/bin/env python3
# 预测脚本 - {target}
# 生成时间：{timestamp.isoformat()}
# 模型：{"多模型自动对比" if model_type == "auto" else model_type}
# 说明：自动训练多个模型，选择最优结果

import json
import sys
import warnings
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

try:
    import pymysql
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"错误：{{e}}")
    sys.exit(1)

# 模型导入（可选）
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    print("⚠️  statsmodels 未安装，跳过 ARIMA/指数平滑模型")

try:
    from sklearn.linear_model import LinearRegression, Lasso
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    from sklearn.preprocessing import StandardScaler
    LINEAR_REGRESSION_AVAILABLE = True
except ImportError:
    LINEAR_REGRESSION_AVAILABLE = False
    print("⚠️  scikit-learn 未安装，跳过线性回归/Lasso 模型")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("⚠️  prophet 未安装，跳过 Prophet 模型")


def load_data(conn):
    """加载历史数据"""
    query = """
    SELECT DATE({date_column}) as date, AVG({metric_column}) as daily_metric
    FROM {table_name}
    WHERE {date_column} >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
    GROUP BY DATE({date_column})
    ORDER BY date
    """
    with conn.cursor() as cursor:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=columns)
    return df


def train_arima(df, forecast_periods):
    """ARIMA 模型"""
    if not ARIMA_AVAILABLE:
        return None
    
    try:
        print("  训练 ARIMA 模型...")
        data = df['daily_metric'].dropna()
        
        # 自动选择最优参数（简化版）
        best_aic = float('inf')
        best_order = (1, 1, 1)
        
        for p in range(3):
            for d in range(2):
                for q in range(3):
                    try:
                        model = ARIMA(data, order=(p, d, q))
                        model_fit = model.fit()
                        if model_fit.aic < best_aic:
                            best_aic = model_fit.aic
                            best_order = (p, d, q)
                    except:
                        continue
        
        print(f"  最优参数：p={{best_order[0]}}, d={{best_order[1]}}, q={{best_order[2]}}")
        model = ARIMA(data, order=best_order)
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=forecast_periods)
        
        # 计算训练误差（sklearn 可能未安装，用 numpy 兜底）
        predictions = model_fit.predict(start=len(data)-30, end=len(data)-1)
        actual = data.iloc[-30:]
        if len(predictions) == len(actual):
            mse = float(np.mean((np.array(actual) - np.array(predictions)) ** 2))
        else:
            mse = float('inf')
        
        return {{
            "model_name": "ARIMA",
            "forecast": forecast.tolist(),
            "params": {{"p": best_order[0], "d": best_order[1], "q": best_order[2]}},
            "metrics": {{"aic": best_aic, "mse": mse}}
        }}
    except Exception as e:
        print(f"  ARIMA 训练失败：{{e}}")
        return None


def train_linear_regression(df, forecast_periods):
    """线性回归模型"""
    if not LINEAR_REGRESSION_AVAILABLE:
        return None
    
    try:
        print("  训练线性回归模型...")
        df_copy = df.copy()
        df_copy['day_index'] = range(len(df_copy))
        
        X = df_copy[['day_index']].values
        y = df_copy['daily_metric'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        future_days = np.arange(len(df), len(df) + forecast_periods).reshape(-1, 1)
        forecast = model.predict(future_days)
        
        # 计算训练误差
        predictions = model.predict(X)
        mse = mean_squared_error(y, predictions)
        mae = mean_absolute_error(y, predictions)
        
        return {{
            "model_name": "Linear Regression",
            "forecast": forecast.tolist(),
            "params": {{"coef": float(model.coef_[0]), "intercept": float(model.intercept_)}},
            "metrics": {{"mse": mse, "mae": mae, "r2": float(model.score(X, y))}}
        }}
    except Exception as e:
        print(f"  线性回归训练失败：{{e}}")
        return None


def train_lasso(df, forecast_periods):
    """Lasso 回归模型（带 L1 正则化）"""
    if not LINEAR_REGRESSION_AVAILABLE:
        return None
    
    try:
        print("  训练 Lasso 回归模型...")
        df_copy = df.copy()
        
        # 构建更多特征（提高 Lasso 的价值）
        df_copy['day_index'] = range(len(df_copy))
        df_copy['day_squared'] = df_copy['day_index'] ** 2
        df_copy['rolling_mean_7'] = df_copy['daily_metric'].rolling(window=7, min_periods=1).mean()
        df_copy['rolling_std_7'] = df_copy['daily_metric'].rolling(window=7, min_periods=1).std()
        
        # 填充 NaN
        df_copy = df_copy.bfill().ffill()
        
        feature_cols = ['day_index', 'day_squared', 'rolling_mean_7', 'rolling_std_7']
        X = df_copy[feature_cols].values
        y = df_copy['daily_metric'].values
        
        # 标准化特征
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # 自动选择最优 alpha 参数
        print("    自动选择最优 alpha 参数...")
        best_alpha = 0.001
        best_mse = float('inf')
        
        for alpha in [0.0001, 0.001, 0.01, 0.1, 1.0]:
            model = Lasso(alpha=alpha, max_iter=10000)
            model.fit(X_scaled, y)
            predictions = model.predict(X_scaled)
            mse = mean_squared_error(y, predictions)
            if mse < best_mse:
                best_mse = mse
                best_alpha = alpha
        
        print(f"    最优 alpha: {{best_alpha}}")
        
        # 使用最优 alpha 重新训练
        model = Lasso(alpha=best_alpha, max_iter=10000)
        model.fit(X_scaled, y)
        
        # 预测未来
        future_indices = np.arange(len(df), len(df) + forecast_periods)
        future_features = np.zeros((forecast_periods, len(feature_cols)))
        future_features[:, 0] = future_indices  # day_index
        future_features[:, 1] = future_indices ** 2  # day_squared
        future_features[:, 2] = df_copy['rolling_mean_7'].iloc[-1]  # 使用最后的滚动均值
        future_features[:, 3] = df_copy['rolling_std_7'].iloc[-1]  # 使用最后的滚动标准差
        
        future_features_scaled = scaler.transform(future_features)
        forecast = model.predict(future_features_scaled)
        
        # 计算训练误差
        predictions = model.predict(X_scaled)
        mse = mean_squared_error(y, predictions)
        mae = mean_absolute_error(y, predictions)
        
        # 计算非零系数（特征选择）
        non_zero_coefs = np.sum(model.coef_ != 0)
        
        return {{
            "model_name": "Lasso Regression",
            "forecast": forecast.tolist(),
            "params": {{
                "alpha": best_alpha,
                "non_zero_coefs": int(non_zero_coefs),
                "coef": [float(c) for c in model.coef_]
            }},
            "metrics": {{"mse": mse, "mae": mae, "r2": float(model.score(X_scaled, y))}}
        }}
    except Exception as e:
        print(f"  Lasso 训练失败：{{e}}")
        return None


def train_exponential_smoothing(df, forecast_periods):
    """指数平滑模型"""
    if not ARIMA_AVAILABLE:
        return None
    
    try:
        print("  训练指数平滑模型...")
        data = df['daily_metric'].dropna()
        
        # 尝试不同组合
        best_model = None
        best_aic = float('inf')
        
        for trend in [None, 'add']:
            for seasonal in [None, 'add']:
                try:
                    model = ExponentialSmoothing(
                        data,
                        trend=trend,
                        seasonal=seasonal,
                        seasonal_periods=7 if len(data) >= 14 else None
                    )
                    model_fit = model.fit()
                    if hasattr(model_fit, 'aic') and model_fit.aic < best_aic:
                        best_aic = model_fit.aic
                        best_model = model_fit
                except:
                    continue
        
        if best_model is None:
            return None
        
        forecast = best_model.forecast(forecast_periods)
        
        return {{
            "model_name": "Exponential Smoothing",
            "forecast": forecast.tolist(),
            "params": {{}},
            "metrics": {{"aic": best_aic}}
        }}
    except Exception as e:
        print(f"  指数平滑训练失败：{{e}}")
        return None


def train_prophet(df, forecast_periods):
    """Prophet 模型"""
    if not PROPHET_AVAILABLE:
        return None
    
    try:
        print("  训练 Prophet 模型...")
        prophet_df = df.copy()
        prophet_df.columns = ['ds', 'y']
        
        model = Prophet(daily_seasonality=True, verbose=False)
        model.fit(prophet_df)
        
        future = model.make_future_dataframe(periods=forecast_periods)
        forecast = model.predict(future)
        
        return {{
            "model_name": "Prophet",
            "forecast": forecast['yhat'].tail(forecast_periods).tolist(),
            "params": {{}},
            "metrics": {{}}
        }}
    except Exception as e:
        print(f"  Prophet 训练失败：{{e}}")
        return None


def select_best_model(results):
    """选择最优模型（基于 MSE）"""
    valid_results = [r for r in results if r is not None and 'mse' in r.get('metrics', {{}})]
    
    if not valid_results:
        # 如果没有 MSE，使用 AIC
        valid_results = [r for r in results if r is not None and 'aic' in r.get('metrics', {{}})]
        if valid_results:
            return min(valid_results, key=lambda x: x['metrics']['aic'])
        return None
    
    return min(valid_results, key=lambda x: x['metrics']['mse'])


def main():
    OUTPUT_FILE = "{output_file}"
    TARGET = "{target}"
    FORECAST_PERIODS = {parameters.get('forecast_periods', 30)}
    
    # 从环境变量读取配置
    import os
    from dotenv import load_dotenv
    load_dotenv("{config.get('env_file', '.env')}")
    
    RDS_HOST = os.getenv("DUCKDB_HOST")
    RDS_PORT = int(os.getenv("DUCKDB_PORT", "3306"))
    RDS_USER = os.getenv("DUCKDB_USER")
    RDS_PASSWORD = os.getenv("DUCKDB_PASSWORD")
    RDS_DATABASE = os.getenv("DUCKDB_DATABASE")
    
    print("=" * 60)
    print(f"开始预测：{{TARGET}}")
    print(f"连接 RDS: {{RDS_HOST}}:{{RDS_PORT}}")
    print(f"预测周期：{{FORECAST_PERIODS}} 天")
    print("=" * 60)
    
    # 连接数据库
    try:
        conn = pymysql.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            user=RDS_USER,
            password=RDS_PASSWORD,
            database=RDS_DATABASE,
            charset="utf8mb4",
            connect_timeout=10
        )
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败：{{e}}")
        return 1
    
    # 加载数据
    print("\\n【步骤 1/3】加载历史数据...")
    df = load_data(conn)
    print(f"✓ 加载了 {{len(df)}} 条数据（{{df['date'].min()}} 至 {{df['date'].max()}}）")
    
    if len(df) < 30:
        print(f"❌ 数据量不足（至少需要 30 条，当前 {{len(df)}} 条）")
        return 1
    
    # 训练多个模型
    print("\\n【步骤 2/3】训练多个模型...")
    models_to_train = {json.dumps(models_to_run)}
    
    results = []
    
    if "arima" in models_to_train:
        result = train_arima(df, FORECAST_PERIODS)
        if result:
            results.append(result)
    
    if "linear_regression" in models_to_train:
        result = train_linear_regression(df, FORECAST_PERIODS)
        if result:
            results.append(result)
    
    if "lasso" in models_to_train:
        result = train_lasso(df, FORECAST_PERIODS)
        if result:
            results.append(result)
    
    if "exponential_smoothing" in models_to_train:
        result = train_exponential_smoothing(df, FORECAST_PERIODS)
        if result:
            results.append(result)
    
    if "prophet" in models_to_train:
        result = train_prophet(df, FORECAST_PERIODS)
        if result:
            results.append(result)
    
    if not results:
        print("❌ 所有模型训练失败")
        return 1
    
    # 选择最优模型
    print("\\n【步骤 3/3】选择最优模型...")
    best_result = select_best_model(results)
    
    if not best_result:
        print("⚠️  无法选择最优模型，使用第一个成功训练的模型")
        best_result = results[0]
    
    print(f"✓ 最优模型：{{best_result['model_name']}}")
    print(f"  评估指标：{{json.dumps(best_result['metrics'], indent=2)}}")
    
    # 保存所有模型结果
    all_results = {{
        "prediction_id": "{prediction_id}",
        "timestamp": datetime.now().isoformat(),
        "target": TARGET,
        "models_trained": len(results),
        "all_models": [
            {{
                "name": r["model_name"],
                "params": r["params"],
                "metrics": r["metrics"]
            }} for r in results
        ],
        "best_model": {{
            "name": best_result["model_name"],
            "params": best_result["params"],
            "metrics": best_result["metrics"],
            "forecast": best_result["forecast"]
        }},
        "forecast_summary": {{
            "mean": float(np.mean(best_result["forecast"])),
            "std": float(np.std(best_result["forecast"])),
            "min": float(np.min(best_result["forecast"])),
            "max": float(np.max(best_result["forecast"]))
        }}
    }}
    
    # 保存结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\\n✓ 预测完成，结果已保存：{{OUTPUT_FILE}}")
    print("=" * 60)
    
    # 输出简要结果
    print("\\n【预测摘要】")
    print(f"最优模型：{{best_result['model_name']}}")
    print(f"平均预测值：{{all_results['forecast_summary']['mean']:.2f}}")
    print(f"预测范围：{{all_results['forecast_summary']['min']:.2f}} - {{all_results['forecast_summary']['max']:.2f}}")
    
    conn.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

    # 写入脚本文件
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    os.chmod(script_file, 0o755)
    
    # 返回配置信息
    return {
        "prediction_id": prediction_id,
        "script_file": str(script_file),
        "output_file": str(output_file),
        "models_to_run": models_to_run,
        "timestamp": timestamp.isoformat()
    }


def main():
    parser = argparse.ArgumentParser(description="生成预测逻辑")
    parser.add_argument("--target", "-t", required=True, help="预测目标描述")
    parser.add_argument("--models", "-m", default="auto", 
                       help="模型选择：auto（自动对比）/ arima / linear_regression / exponential_smoothing / prophet")
    parser.add_argument("--periods", "-p", type=int, default=30, help="预测周期（天数）")
    parser.add_argument("--table", default="your_table", help="数据表名")
    parser.add_argument("--date-column", default="created_at", help="日期列名")
    parser.add_argument("--metric-column", default="metric_value", help="指标列名")
    parser.add_argument("--env-file", "-e", default=".env", help=".env 文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径")
    
    args = parser.parse_args()
    
    # 加载配置
    load_dotenv(args.env_file)
    config = {
        "rds": {
            "host": os.getenv("DUCKDB_HOST"),
            "port": int(os.getenv("DUCKDB_PORT", "3306")),
            "user": os.getenv("DUCKDB_USER"),
            "password": os.getenv("DUCKDB_PASSWORD"),
            "database": os.getenv("DUCKDB_DATABASE")
        },
        "records_dir": os.getenv("RECORDS_DIR", "/home/admin/.openclaw/workspace/skills/alibabacloud-rds-duckdb-analytics-skill/records"),
        "env_file": args.env_file
    }
    
    parameters = {
        "forecast_periods": args.periods,
        "table": args.table,
        "date_column": args.date_column,
        "metric_column": args.metric_column
    }
    
    # 生成预测脚本
    prediction_config = generate_script(args.target, args.models, parameters, config)
    
    # 输出
    result = {
        "success": True,
        "prediction_id": prediction_config["prediction_id"],
        "script_file": prediction_config["script_file"],
        "models_to_run": prediction_config["models_to_run"],
        "message": f"预测脚本已生成，支持 {len(prediction_config['models_to_run'])} 个模型自动对比"
    }
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
