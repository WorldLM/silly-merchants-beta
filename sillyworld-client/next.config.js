/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: '.next',
  pageExtensions: ['js', 'jsx', 'ts', 'tsx'],
  experimental: {
    serverComponentsExternalPackages: ['tailwindcss']
  },
  async redirects() {
    return [
      {
        source: "/home",
        destination: "/",
        permanent: true,
      },
      // 捕获任何尝试访问/home/后面带参数的请求
      {
        source: "/home/:path*",
        destination: "/:path*",
        permanent: true,
      }
    ]
  }
}

module.exports = nextConfig 