import {defineConfig} from 'vitepress'
import {withMermaid} from 'vitepress-plugin-mermaid'

// https://vitepress.dev/reference/site-config
export default withMermaid(defineConfig({
    title: "MediaCrawler Pro",
    description: "Upgraded edition of MediaCrawler — multi-platform social crawler with WebUI, desktop, tasks, AI chat, and MCP.",
    lastUpdated: true,
    base: '/MediaCrawler-Pro/',
    themeConfig: {
        editLink: {
            pattern: 'https://github.com/Viyozc/MediaCrawler-Pro/tree/main/docs/:path'
        },
        search: {
            provider: 'local'
        },
        nav: [
            {text: '首页', link: '/'},
            {text: 'GitHub', link: 'https://github.com/Viyozc/MediaCrawler-Pro'},
            {text: '贡献', link: 'https://github.com/Viyozc/MediaCrawler-Pro/blob/main/CONTRIBUTING.md'},
        ],

        sidebar: [
            {
                text: 'MediaCrawler Pro 文档',
                items: [
                    {text: '基本使用', link: '/'},
                    {text: 'MCP 服务', link: '/MCP服务使用指南'},
                    {text: 'CDP 模式', link: '/CDP模式使用指南'},
                    {text: '常见问题', link: '/常见问题'},
                    {text: 'IP 代理使用', link: '/代理使用'},
                    {text: '词云图使用', link: '/词云图使用配置'},
                    {text: '数据存储', link: '/data_storage_guide'},
                    {text: '手机号登录说明', link: '/手机号登录说明'},
                ]
            },
            {
                text: '致谢',
                items: [
                    {text: '上游 MediaCrawler', link: 'https://github.com/NanmiCoder/MediaCrawler'}
                ]
            },
        ],

        socialLinks: [
            {icon: 'github', link: 'https://github.com/Viyozc/MediaCrawler-Pro'}
        ]
    }
}))
