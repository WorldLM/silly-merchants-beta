/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: '.next',
  dir: 'src',
  async redirects() {
    return [
      {
        source: '/',
        destination: '/home',
        permanent: true,
      },
    ]
  },
}

module.exports = nextConfig 