# 发布成网站

## 目标
让学员打开一个链接就能学习，例如：

```
https://你的用户名.github.io/my-course/
```

## 最简单的方式：直接发布一个网页
1. 仓库里放一个 `index.html`。
2. 进入仓库 **Settings → Pages**。
3. **Source** 选 `Deploy from a branch`，分支选 `main`，目录选 `/ (root)`。
4. 保存，等 1~2 分钟，页面顶部会显示网站地址。

## 更适合做课程的方式：用 Markdown 写，自动生成网站
直接写网页很累。更常见的做法是：**用 Markdown 写文章，工具自动生成带目录、搜索的网站**。本站就是这样做的，使用 MkDocs。

### 本地预览

```bash
pip install mkdocs-material
mkdocs serve
```

浏览器打开 `http://127.0.0.1:8000`，改文件会自动刷新。

### 自动发布
仓库里放一个 GitHub Actions 配置（本站 `.github/workflows/deploy.yml`）。以后每次 `git push`，GitHub 会自动：

1. 构建网站
2. 发布到 Pages

你只管写内容，不用手动发布。

!!! note "第一次需要手动打开一个开关"
    进入 **Settings → Pages**，把 **Source** 设为 **GitHub Actions**。只需要设置一次。

## 给学员发链接前的检查清单

- [ ] 手机上打开过，排版正常
- [ ] 所有示例数据都是虚构的
- [ ] 没有密码、密钥、真实客户信息
- [ ] 链接在无痕窗口能打开（说明确实是公开的）
