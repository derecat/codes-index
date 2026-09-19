/* 站点配置 —— 只改这个文件，不用动 app.js */
window.__SITE_CONFIG__ = {
  /* 仓库地址 */
  repo: 'https://github.com/derecat/codes-index',

  /* 评论功能，基于 giscus（把 GitHub Discussions 当成评论后端，免费、零服务器）
   *
   * 已经帮你填好了 repoId / categoryId。唯一还差一步：
   * 安装 giscus App → https://github.com/apps/giscus
   *   Install → 选择 derecat/codes-index → 完成授权
   * 装完之后评论区立刻可用（刷新页面即可）。
   *
   * 用的是 Announcements 分类：只有维护者能开新帖，但任何人都能回复。
   * 讨论串由 giscus 在第一条评论时自动创建，标题就是番号本身。
   *
   * 想换成别的分类也行：在 Discussions 里建好分类后，
   * 用 GraphQL 查它的 id（见 README「评论区」一节），替换下面两项即可。
   */
  giscus: {
    repo: 'derecat/codes-index',
    repoId: 'R_kgDOUg5ttg',
    category: 'Announcements',
    categoryId: 'DIC_kwDOUg5tts4DF7UM'
  }
};
