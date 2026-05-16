import { useMemo, useState } from 'react'
import mockPrediction from '../data/mockPrediction.json'

const priorityClassNames = {
  HIGH: 'bg-orange-100 text-orange-700',
  MEDIUM: 'bg-yellow-100 text-yellow-700',
  LOW: 'bg-slate-200 text-slate-600',
}

const papers = ['Paper 1', 'Paper 2']

function Dashboard() {
  const [selectedPaper, setSelectedPaper] = useState('Paper 1')

  const filteredTopics = useMemo(() => {
    return mockPrediction.topics
      .filter((topic) => topic.paper === selectedPaper)
      .sort((a, b) => b.appearance_rate - a.appearance_rate)
  }, [selectedPaper])

  const years = `${mockPrediction.range.start_year}-${mockPrediction.range.end_year}`

  return (
    <main className="min-h-screen p-4 text-slate-800 sm:p-6">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
        <header className="rounded-2xl bg-slate-900 p-5 text-white shadow-sm sm:p-6">
          <p className="text-sm font-medium text-slate-300">Rony Prep Student Dashboard</p>
          <h1 className="mt-1 text-2xl font-bold sm:text-3xl">Study Smart, Not Hard</h1>
          <p className="mt-2 text-sm text-slate-300">
            Prioritized trend insights to focus revision on the most likely KCSE topics.
          </p>
        </header>

        <section className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4 text-emerald-900 shadow-sm">
          <p className="text-sm font-semibold">Exam Coverage Summary</p>
          <p className="mt-1 text-sm">
            Probability model covers {mockPrediction.range.total_years_in_range} years ({years}) and
            tracks {mockPrediction.topics.length} high-impact topics.
          </p>
        </section>

        <section className="rounded-2xl bg-white p-4 shadow-sm sm:p-5">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-lg font-semibold">Trend Matrix</h2>
            <div className="inline-flex rounded-lg bg-slate-100 p-1">
              {papers.map((paper) => (
                <button
                  key={paper}
                  type="button"
                  onClick={() => setSelectedPaper(paper)}
                  className={`rounded-md px-3 py-2 text-sm font-medium transition ${
                    selectedPaper === paper
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {paper}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-4 font-semibold">Topic</th>
                  <th className="py-2 pr-4 font-semibold">Section</th>
                  <th className="py-2 pr-4 font-semibold">Appearance</th>
                  <th className="py-2 pr-4 font-semibold">Avg Marks</th>
                  <th className="py-2 font-semibold">Priority</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredTopics.map((topic) => (
                  <tr key={`${topic.topic}-${topic.paper}`}>
                    <td className="py-3 pr-4 font-medium text-slate-900">{topic.topic}</td>
                    <td className="py-3 pr-4 text-slate-600">{topic.section}</td>
                    <td className="py-3 pr-4 text-slate-600">
                      {Math.round(topic.appearance_rate * 100)}%
                    </td>
                    <td className="py-3 pr-4 text-slate-600">{topic.average_marks}</td>
                    <td className="py-3">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
                          priorityClassNames[topic.priority] ?? priorityClassNames.LOW
                        }`}
                      >
                        {topic.priority}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  )
}

export default Dashboard
