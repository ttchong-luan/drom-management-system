# drom-management-system
基于Vue3+Element Plus的学生宿舍管理系统（前端），实现多角色权限控制、报修管理、宿舍信息管理等功能基于Vue3+Element Plus的学生宿舍管理系统（前端），实现多角色权限控制、报修管理、宿舍信息管理等功能
## 技术栈
- 核心框架：Vue 3（组合式API）、Vite
- 状态管理：Pinia
- 路由：Vue Router 4（路由守卫实现权限控制）
- UI 组件：Element Plus
- 网络请求：Axios（封装请求/响应拦截）
- 其他：Dayjs（时间处理）

## 核心功能
1. 多角色登录与权限控制：学生/宿管/管理员不同权限拦截；
2. 宿舍信息管理：楼栋/房间/床位信息展示、分配与调整；
3. 报修管理：报修申请、进度查询、宿管接单处理；
4. 公告管理：公告发布、查看、分类展示；
## 本地运行步骤
1. 克隆仓库
```bash
git clone https://github.com/ttchong-luan/drom-management-system.git
2.进入项目目录
cd drom-management-system
3.安装依赖
npm install
4.启动开发服务器
npm run dev
5.访问地址：http://localhost:5173
