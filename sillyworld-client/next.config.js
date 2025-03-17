/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: '.next',
  async redirects() {
    return [
      {
        source: '/',
        destination: '/home',
        permanent: true,
      },
    ]
  },
  experimental: {
    appDir: true
  }
}

module.exports = nextConfig 