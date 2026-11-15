export default function Login() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg w-full max-w-md border border-gray-700">
        <h2 className="text-2xl font-bold text-white mb-6 text-center">Login to Quantum Lab</h2>
        <form className="flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
            <input type="email" className="w-full bg-gray-900 border border-gray-700 rounded-md p-2 text-white focus:outline-none focus:border-blue-500" placeholder="user@example.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
            <input type="password" className="w-full bg-gray-900 border border-gray-700 rounded-md p-2 text-white focus:outline-none focus:border-blue-500" placeholder="••••••••" />
          </div>
          <button type="button" className="mt-4 w-full bg-blue-600 text-white font-semibold py-2 rounded-md hover:bg-blue-700 transition-colors">
            Sign In
          </button>
        </form>
      </div>
    </div>
  );
}
