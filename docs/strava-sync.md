# Strava 数据自动对齐

Vercel 网站的数据来自本仓库的 `src/static/activities.json`。GitHub Actions
每小时第 17 分钟尝试完整抓取 Strava，更新数据库、地图数据和运动统计，再推送到仓库。
GitHub 的定时任务可能延迟；页面还需等待 Vercel 构建，因此不是严格实时。

## 删除与合并活动

定时同步启用 `--prune-deleted`：完整读取 Strava 所有分页后，移除本地已不在
Strava 返回列表中的活动。只清理 `source=strava` 的记录，不影响 GPX 等来源，
也不在 Strava 上进行任何写入。

例如在 Strava 删除每日骑行、保留合并轨迹，下次成功同步后地图和统计只保留合并轨迹。
如果两种轨迹在 Strava 上都还存在，网站也会保留两种轨迹；不会根据名称或路线自动去重。
网站以当前授权能够访问的 Strava 活动为准，权限变化导致不可见的活动也会被移除。

API 分页失败、限流、数据处理异常或完整结果为空时，同步失败并保留原数据。
空结果保护意味着，如果主动删除了 Strava 上的全部活动，需要另行确认清空本地数据。
开始抓取时点之后的本地活动不参与本次清理。

## 手动立即对齐

在 GitHub 的 **Actions → Run Data Sync → Run workflow** 中选择 `master` 运行。
此操作使用已有的 Strava Secrets，不需要新增密钥。首次合并同步代码也会触发一次对齐。
Vercel 项目应连接 `yslemmo/workouts_page` 的 `master` 生产分支，并允许该分支自动部署。
没有数据变化时不产生提交，也不需要重新部署。

同步流程不再调用 GitHub Pages 发布，因为网站部署在 Vercel。
推送失败会明确报错，避免把“抓取成功但网站数据未更新”误报成成功。

本地验证（不连接 Strava）：

```sh
python -m unittest discover -s tests -v
```
