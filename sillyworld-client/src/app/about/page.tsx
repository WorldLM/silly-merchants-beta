import Link from 'next/link'

export default function About() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-6">About SillyWorld</h1>
        <p className="mb-4">This is a demo project with Next.js frontend and FastAPI backend.</p>
        <div className="mt-6">
          <Link href="/" className="text-blue-500 hover:text-blue-700">
            Home
          </Link>
        </div>
      </div>
    </main>
  )
} 