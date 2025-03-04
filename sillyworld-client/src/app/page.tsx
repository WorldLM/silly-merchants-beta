import { redirect } from 'next/navigation';
import Link from 'next/link';

export default function Home() {
  redirect('/home');
}

// Remove the second default export
// export default function Home() {
//   return (
//     <main className="flex min-h-screen flex-col items-center justify-between p-24">
//       <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
//         <h1 className="text-4xl font-bold mb-6">Welcome to SillyWorld</h1>
//         <p className="mb-4">A fun and silly place to explore!</p>
//         <div className="mt-6 flex space-x-4">
//           <Link href="/about" className="text-blue-500 hover:text-blue-700">
//             About
//           </Link>
//           <Link href="/home" className="text-blue-500 hover:text-blue-700">
//             Home Page
//           </Link>
//         </div>
//       </div>
//     </main>
//   )
// } 