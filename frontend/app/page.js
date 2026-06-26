import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-extrabold text-slate-800 tracking-tight">
        🌲 Pine Sales AI
      </h1>
      <p className="text-slate-500 text-center max-w-md">
        Multi-tenant B2B SaaS — AI Voice Agents + Real-Time Kitchen Display System
      </p>
      <div className="flex gap-4 flex-wrap justify-center">
        <Link href="/dashboard/demo-tenant"
          className="bg-indigo-500 hover:bg-indigo-600 text-white font-bold
                     px-6 py-3 rounded-2xl transition-colors shadow-md shadow-indigo-100">
          Business Dashboard
        </Link>
        <Link href="/kitchen/demo-tenant"
          className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold
                     px-6 py-3 rounded-2xl transition-colors shadow-md shadow-emerald-100">
          Kitchen Monitor
        </Link>
      </div>
    </main>
  );
}
