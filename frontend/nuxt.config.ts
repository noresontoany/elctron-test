import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2026-11-01',
  ssr: false,
  devtools: { enabled: false },
  modules: ['shadcn-nuxt'],
  shadcn: { prefix: '', componentDir: './src/shared/ui' },
  alias: { '@': new URL('./src', import.meta.url).pathname },
  css: ['@/shared/styles/main.css'],
  vite: { plugins: [tailwindcss()] },
  app: {
    head: {
      title: 'Spoke — веломастерская',
      htmlAttrs: { lang: 'ru' },
      meta: [
        {
          name: 'description',
          content: 'Рабочее пространство веломастерской. Заказы в одном ритме.',
        },
      ],
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
    },
  },
})
