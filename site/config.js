/* 站点配置 —— 只改这个文件，不用动 app.js
 * 部署前请把下面三项换成你自己的。
 */
window.__SITE_CONFIG__ = {
  /* 你的仓库地址（站点右上角和「提投稿」按钮会用到） */
  repo: 'https://github.com/derecat/codes-index',

  /* 评论功能，基于 giscus（把 GitHub Discussions 当成评论后端，免费、零服务器）
   * 配置步骤：
   *   1. 仓库 Settings → General → Features 勾上 Discussions
   *   2. Discussions 里新建分类，名字随意（建议「条目讨论」），
   *      类型选 Announcements —— 只有机器人能发帖，防止灌水
   *   3. 安装 giscus App：https://github.com/apps/giscus → 授权本仓库
   *   4. 打开 https://giscus.app ，填入仓库名和分类名，
   *      页面底部会生成 repoId / categoryId，复制过来贴上即可
   * 留空则不显示评论区，只显示一个「去 GitHub 讨论」的入口。
   */
  giscus: {
    repo: '',            // 形如 'yourname/codes-index'
    repoId: '',          // 形如 'R_kgDOLxxxxxxx'
    category: '条目讨论',  // Discussions 分类名
    categoryId: ''       // 形如 'DIC_kwDOLxxxxxxx'
  }
};
