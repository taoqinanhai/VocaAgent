# VocaAgent-2.0

AI 职业规划平台 — 基于阿里云百炼 DashScope 的 4-Agent 流水线系统。

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/taoqinanhai/VocaAgent.git
cd VocaAgent
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，填入你自己的百炼 API Key 和 APP_ID：

```env
DB_PASSWORD=你的数据库密码
API_KEY=sk-你的百炼API-Key
APP_ID_A=你的百炼APP_ID
APP_ID_B=你的百炼APP_ID
APP_ID_C=你的百炼APP_ID
APP_ID_D=你的百炼APP_ID
APP_ID_E=你的百炼APP_ID
```

### 3. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 4. 初始化数据库

确保 MySQL 已安装并运行，然后：

```bash
python init_database.py --import-excel
```

这会自动创建 `vocaagent` 数据库、12 张表，并从 Excel 导入岗位数据。

### 5. 启动后端

```bash
python app.py
```

后端运行在 http://localhost:5000

### 6. 安装并启动前端

```bash
cd ../frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Flask + MySQL + 阿里云百炼 DashScope |
| 前端 | Vue 3 + TypeScript + Element Plus + ECharts |
| AI | DashScope Application API（SSE 流式） |

## 项目结构

```
├── backend/          # Flask 后端
│   ├── routes/       # API 路由
│   ├── services/     # Agent 编排服务
│   ├── config/       # 配置中心
│   └── utils/        # 工具函数
├── frontend/         # Vue 3 前端
│   ├── src/views/    # 页面组件
│   ├── src/stores/   # Pinia 状态管理
│   └── dist/         # 构建产物
└── docs/             # 设计文档
```

## License

MIT
