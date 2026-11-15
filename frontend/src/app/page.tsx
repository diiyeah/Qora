import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-900 text-white">
      <h1 className="text-6xl font-bold mb-8 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
        Quantum Lab
      </h1>
      <p className="text-xl mb-12 text-gray-300">
        Interactive Quantum Learning Platform
      </p>
      
      <div className="flex gap-4">
        <Link href="/learning" className="px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors">
          Learning Mode
        </Link>
        <Link href="/development" className="px-6 py-3 rounded-lg bg-purple-600 hover:bg-purple-700 transition-colors">
          Development Mode
        </Link>
      </div>

      <div className="mt-12 flex gap-4 text-sm text-gray-400">
        <Link href="/auth/login" className="hover:text-white transition-colors">Login</Link>
        <Link href="/auth/signup" className="hover:text-white transition-colors">Sign Up</Link>
      </div>
    </main>
  );
}
