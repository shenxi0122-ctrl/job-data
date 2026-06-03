# Streamlit 部署说明

## 需要上传到 GitHub 的最小文件

- `streamlit_app.py`
- `app_dashboard.py`
- `requirements.txt`
- `output/51job_sample_10000_enhanced.csv`
- `output/51job_job_alerts.csv`
- `output/salary_factor_coefficients.csv`

## 部署步骤

1. 新建一个 GitHub 仓库。
2. 把上面这些文件上传到仓库根目录。
3. 打开 [Streamlit Community Cloud](https://streamlit.io/cloud)。
4. 选择你的仓库。
5. 主文件填写 `streamlit_app.py`。
6. 部署完成后，平台会给你一个可公开访问的 URL。

## 注意

- 不要上传 `51job数据_合并.csv` 和 `51job_cleaned_full.csv`，文件太大，没必要。
- 这个 URL 是公开的，别人直接可以打开。
