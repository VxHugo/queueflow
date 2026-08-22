function App() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div><span className="text-lg font-semibold tracking-tight">Queue</span><span className="text-cyan-400">Flow</span></div>
          <span className="rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-xs font-medium text-amber-200">Foundation in progress</span>
        </div>
      </header>
      <section className="mx-auto max-w-7xl px-6 py-20">
        <p className="text-sm font-medium uppercase tracking-[0.24em] text-cyan-400">Distributed job processing</p>
        <h1 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight sm:text-6xl">A clear operational view of work that never blocks your product.</h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-400">The QueueFlow dashboard will show real queues, workers, retries and recovery events as the platform is built across the delivery milestones.</p>
        <div className="mt-12 grid gap-4 sm:grid-cols-3">
          {[
            ['API', 'FastAPI service is being checked against PostgreSQL and Redis.'],
            ['Infrastructure', 'Local Compose brings up the database, cache and web surface.'],
            ['Next', 'Job domain and durable state arrive in milestone two.'],
          ].map(([title, copy]) => <article key={title} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5"><h2 className="font-medium text-cyan-200">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-400">{copy}</p></article>)}
        </div>
      </section>
    </main>
  )
}

export default App
