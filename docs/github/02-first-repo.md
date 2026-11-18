# 建第一个仓库

## 准备
1. 注册一个 GitHub 账号（用邮箱即可）。
2. 电脑上安装 Git（Mac 在终端输入 `git --version`，没有会提示安装）。

## 第一步：在网页上建仓库
1. 登录后点右上角 **+** → **New repository**。
2. 填仓库名，例如 `my-course`。
3. 选 **Public**（公开）。
4. 勾选 **Add a README file**。
5. 点 **Create repository**。

到这里，你已经有了一个仓库。

## 第二步：把仓库下载到电脑
在终端运行（把 `你的用户名` 换成自己的）：

```bash
git clone https://github.com/你的用户名/my-course.git
```

## 第三步：改文件并“存档”
进入文件夹，新建或修改文件后：

```bash
cd my-course
git add .
git commit -m "新增第一章"
git push
```

这三条的含义：

| 命令 | 大白话 |
|---|---|
| `git add .` | 把这次改动放进“待存档”篮子 |
| `git commit -m "说明"` | 存档，并写一句话说明 |
| `git push` | 把存档上传到 GitHub |

!!! tip "没有命令行基础？"
    可以直接在 GitHub 网页上点文件旁的铅笔图标编辑，保存时选 **Commit changes**，效果一样。

## 常见问题

??? question "push 时要我输入密码，但密码不对"
    GitHub 已不支持用账号密码推送。推荐安装官方命令行工具 `gh`，运行 `gh auth login` 按提示登录一次即可。

??? question "提示 failed to push / rejected"
    通常是网页上有改动而本地没有。先运行 `git pull`，再 `git push`。
